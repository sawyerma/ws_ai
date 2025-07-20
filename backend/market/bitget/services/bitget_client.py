import asyncio
import json
import logging
import websockets
import time
from datetime import datetime, timezone
from typing import List
from market.bitget.config import bitget_config, TLS_CONFIG
from market.bitget.utils.adaptive_rate_limiter import AdaptiveRateLimiter
from market.bitget.storage.redis_manager import redis_manager
from market.bitget.api.ws_manager import broadcast_trade_data
from market.bitget.services.auto_remediation import bitget_failover_active

logger = logging.getLogger("bitget-client")

class BitgetWebSocketClient:
    def __init__(self, symbols: List[str], market_type: str):
        # Support für Symbolgruppen statt einzelne Symbole
        self.symbols = symbols if isinstance(symbols, list) else [symbols]
        self.market_type = market_type
        
        # Get market-specific configuration
        self.market_config = bitget_config.market_mappings.get(market_type)
        if not self.market_config:
            raise ValueError(f"Unsupported market type: {market_type}")
            
        self.ws_url = self.market_config["ws_url"]
        self.inst_type = self.market_config["inst_type"] 
        self.symbol_suffix = self.market_config["suffix"]
        
        self.running = False
        self.reconnect_count = 0
        
        # Dynamische Rate Limiter Konfiguration
        self.rate_limiter = AdaptiveRateLimiter(f"ws-{market_type}-{len(self.symbols)}symbols")
        self.rate_limiter.update_base_rps(bitget_config.effective_max_rps)
        
        # Statistiken für Symbolgruppe
        self.connected_symbols = set()
        self.last_data_time = {}
        
    async def start(self):
        if bitget_failover_active:
            logger.info(f"⏭️  Skipping Bitget for {len(self.symbols)} symbols (failover active)")
            return
            
        self.running = True
        logger.info(f"🚀 Starting Bitget client for {len(self.symbols)} symbols ({self.market_type})")
        
        while self.running:
            try:
                await self._connect_and_listen()
            except Exception as e:
                self.reconnect_count += 1
                logger.error(f"❌ Connection failed ({self.reconnect_count}): {e}")
                
                # Exponential backoff mit Maximum
                backoff_time = min(2 ** self.reconnect_count, 60)
                await asyncio.sleep(backoff_time)
                
    async def _connect_and_listen(self):
        """Verbindet und hört auf WebSocket-Nachrichten für alle Symbole"""
        try:
            async with websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
                **TLS_CONFIG
            ) as ws:
                logger.info(f"✅ Connected to {self.ws_url} for {len(self.symbols)} symbols ({self.market_type})")
                
                # Alle Symbole in dieser Gruppe abonnieren
                await self._subscribe_all_symbols(ws)
                
                # Reset reconnect counter bei erfolgreicher Verbindung
                self.reconnect_count = 0
                
                async for message in ws:
                    if not self.running:
                        break
                    await self._process_message(message)
                    
        except Exception as e:
            logger.error(f"❌ WebSocket connection error: {e}")
            raise
                
    async def _subscribe_all_symbols(self, ws):
        """Abonniert alle Symbole in der Gruppe"""
        start_time = time.time()
        
        try:
            # Erstelle Abonnement-Args für alle Symbole
            args = []
            for symbol in self.symbols:
                inst_id = f"{symbol}{self.symbol_suffix}"
                args.append({
                    "instType": self.inst_type,
                    "channel": "trade",
                    "instId": inst_id
                })
                
                # Premium-Feature: Orderbuch für jedes Symbol hinzufügen
                if bitget_config.is_premium:
                    args.append({
                        "instType": self.inst_type,
                        "channel": "books50",  # 50-Level Orderbuch
                        "instId": inst_id,
                        "snapshot": True
                    })
            
            # Subscription-Message senden
            msg = {
                "op": "subscribe",
                "args": args
            }
            
            await self.rate_limiter.acquire()
            await ws.send(json.dumps(msg))
            
            response_time = time.time() - start_time
            self.rate_limiter.report_success()
            
            logger.info(f"📡 Subscribed to {len(self.symbols)} symbols with {len(args)} channels")
            
        except Exception as e:
            self.rate_limiter.report_error(e)
            logger.error(f"❌ Subscription error: {e}")
            raise
            
    async def _process_message(self, message: str):
        """Verarbeitet eingehende WebSocket-Nachrichten für alle Symbole"""
        try:
            msg = json.loads(message)
            
            # Erfolgsmeldung nach Abonnement
            if msg.get("event") == "subscribe":
                logger.info(f"✅ Subscription confirmed for {len(self.symbols)} symbols")
                return
                
            # Fehlermeldungen behandeln
            if msg.get("event") == "error":
                error_msg = msg.get("msg", "Unknown error")
                self.rate_limiter.report_error(Exception(f"API Error: {error_msg}"))
                logger.error(f"❌ WebSocket error: {error_msg}")
                return
            
            # Daten-Updates verarbeiten
            if msg.get("action") == "update":
                channel = msg.get("arg", {}).get("channel", "")
                data = msg.get("data", [])
                
                if channel == "trade":
                    await self._process_trades(data, msg.get("arg", {}))
                elif channel == "books50" and bitget_config.is_premium:
                    await self._process_orderbook(data, msg.get("arg", {}))
                    
            self.rate_limiter.report_success()
                    
        except Exception as e:
            self.rate_limiter.report_error(e)
            logger.error(f"❌ Message processing error: {e}")
            
    async def _process_trades(self, trades: list, channel_info: dict):
        """Verarbeitet Trade-Daten für ein bestimmtes Symbol"""
        inst_id = channel_info.get("instId", "")
        
        # Symbol aus inst_id extrahieren (entfernt Suffix)
        symbol = inst_id.replace(self.symbol_suffix, "") if inst_id else ""
        
        if symbol not in self.symbols:
            logger.warning(f"⚠️  Received trade for unknown symbol: {symbol}")
            return
        
        # Zeitstempel für Aktivitätstracking aktualisieren
        self.last_data_time[symbol] = time.time()
        self.connected_symbols.add(symbol)
        
        for trade_data in trades:
            try:
                trade = self._parse_trade(trade_data, symbol)
                
                # Store in Redis
                await redis_manager.add_trade(symbol, trade, self.market_type)
                
                # Broadcast via WebSocket
                await broadcast_trade_data(symbol, trade)
                
            except Exception as e:
                logger.error(f"❌ Trade processing error for {symbol}: {e}")
    
    async def _process_orderbook(self, orderbook_data: list, channel_info: dict):
        """Verarbeitet Orderbuch-Daten (Premium Feature)"""
        inst_id = channel_info.get("instId", "")
        symbol = inst_id.replace(self.symbol_suffix, "") if inst_id else ""
        
        if symbol not in self.symbols:
            return
        
        try:
            for book_data in orderbook_data:
                # Orderbuch-Verarbeitung (vereinfacht)
                await redis_manager.add_orderbook(symbol, book_data, self.market_type)
                
        except Exception as e:
            logger.error(f"❌ Orderbook processing error for {symbol}: {e}")
                
    def _parse_trade(self, trade_data: list, symbol: str) -> dict:
        """Parsed Trade-Daten für ein bestimmtes Symbol"""
        # Structure: [timestamp, price, size, side]
        ts_ms = int(trade_data[0])
        price = float(trade_data[1])
        size = float(trade_data[2])
        side = trade_data[3].lower()
        
        return {
            "symbol": symbol,
            "market_type": self.market_type,
            "price": price,
            "size": size,
            "side": side,
            "ts": datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
            "timestamp": ts_ms
        }
    
    def get_connection_stats(self) -> dict:
        """Gibt Verbindungsstatistiken zurück"""
        now = time.time()
        active_symbols = [
            symbol for symbol, last_time in self.last_data_time.items()
            if now - last_time < 60  # Aktiv in letzten 60 Sekunden
        ]
        
        return {
            "market_type": self.market_type,
            "total_symbols": len(self.symbols),
            "connected_symbols": len(self.connected_symbols),
            "active_symbols": len(active_symbols),
            "reconnect_count": self.reconnect_count,
            "rate_limiter_stats": self.rate_limiter.get_stats(),
            "symbols": self.symbols,
            "active_symbols_list": active_symbols
        }
        
    async def stop(self):
        """Stoppt WebSocket-Client für alle Symbole"""
        self.running = False
        logger.info(f"🛑 Stopped Bitget client for {len(self.symbols)} symbols ({self.market_type})")
