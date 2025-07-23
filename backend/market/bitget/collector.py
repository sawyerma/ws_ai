import asyncio
import logging
import time
from datetime import datetime, timezone
from market.bitget.services.bitget_client import BitgetWebSocketClient
from market.bitget.storage.redis_manager import redis_manager
from market.bitget.config import system_config, bitget_config
from backend.core.services.aggregator import UnifiedCandleAggregator
from models.trade import UnifiedTrade, MarketType

logger = logging.getLogger("collector")

# Globale Collector Registry für Bitget
bitget_collectors = {}

class BitgetCollector:
    """Hochleistungs-Collector für Bitget Marktdaten"""
    
    def __init__(self, symbol: str, market_type: str, data_queue: asyncio.Queue):
        self.symbol = symbol
        self.market_type = market_type
        self.data_queue = data_queue
        self.client = BitgetWebSocketClient([symbol], market_type)
        self.running = False
        self.process_task = None
        
        # UnifiedCandleAggregator für verschiedene Resolutions
        self.aggregators = {
            res: UnifiedCandleAggregator(res) 
            for res in [1, 60, 300, 900]  # 1s, 1m, 5m, 15m
        }
        self.flush_task = None
        
    async def start(self):
        """Startet den Collector mit maximaler Performance"""
        if self.running:
            return
            
        self.running = True
        
        # Starte Datenverarbeitung parallel
        self.process_task = asyncio.create_task(self._process_data())
        
        # Starte periodisches Candle-Flushing
        self.flush_task = asyncio.create_task(self._periodic_flush())
        
        # WebSocket Client starten
        await self.client.start()
        
        logger.info(f"🚀 Collector started for {self.symbol} ({self.market_type})")
        
    async def _process_data(self):
        """Verarbeitet eingehende Daten mit minimaler Latenz"""
        while self.running:
            # Hier würden normalerweise Daten aus dem WebSocket kommen
            # Für dieses Beispiel simulieren wir Daten
            await asyncio.sleep(0.1)
            trade_data = {
                "symbol": self.symbol,
                "market": self.market_type,
                "price": 50000.0 + (0.1 * (id(self) % 100)),
                "size": 0.01,
                "side": "buy" if (id(self) % 2) == 0 else "sell",
                "ts": int(time.time() * 1000),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Konvertiere zu UnifiedTrade
            unified_trade = UnifiedTrade(
                exchange="bitget",
                symbol=trade_data["symbol"],
                market=MarketType[self.market_type] if self.market_type in MarketType.__members__ else MarketType.spot,
                price=trade_data["price"],
                size=trade_data["size"],
                side=trade_data["side"],
                timestamp=datetime.now(timezone.utc),
                exchange_id=str(trade_data["ts"])
            )
            
            # Verwende UnifiedCandleAggregator
            for aggregator in self.aggregators.values():
                candle = aggregator.process_trade(unified_trade)
                if candle:
                    # Hier würde normalerweise in ClickHouse gespeichert werden
                    logger.debug(f"Generated candle: {candle['resolution']}s for {self.symbol}")
            
            # Zur Weiterverarbeitung in die Queue geben
            await self.data_queue.put(trade_data)
            
            # In Redis speichern
            await redis_manager.add_trade(
                trade_data["symbol"],
                trade_data,
                self.market_type
            )
    
    async def _periodic_flush(self):
        """Flusht alle Candles regelmäßig (alle 30 Sekunden)"""
        while self.running:
            await asyncio.sleep(30)
            try:
                for aggregator in self.aggregators.values():
                    candles = aggregator.flush_all()
                    for candle in candles:
                        # Hier würde normalerweise in ClickHouse gespeichert werden
                        logger.debug(f"Flushed candle: {candle['resolution']}s for {self.symbol}")
            except Exception as e:
                logger.error(f"Periodic flush error: {str(e)}")

    async def stop(self):
        """Stoppt den Collector mit sofortiger Wirkung"""
        if not self.running:
            return
            
        self.running = False
        
        # Client stoppen
        await self.client.stop()
        
        # Verarbeitungstask beenden
        if self.process_task:
            self.process_task.cancel()
            try:
                await self.process_task
            except asyncio.CancelledError:
                pass
        
        # Flush-Task beenden
        if self.flush_task:
            self.flush_task.cancel()
            try:
                await self.flush_task
            except asyncio.CancelledError:
                pass
        
        # Finales Flushing aller Candles
        for aggregator in self.aggregators.values():
            candles = aggregator.flush_all()
            for candle in candles:
                logger.debug(f"Final flush candle: {candle['resolution']}s for {self.symbol}")
                
        logger.info(f"🛑 Collector stopped for {self.symbol} ({self.market_type})")
    
    def get_status(self) -> dict:
        """Gibt aktuellen Status zurück (für Monitoring)"""
        return {
            "symbol": self.symbol,
            "market_type": self.market_type,
            "running": self.running,
            "queue_size": self.data_queue.qsize(),
            "stats": self.client.get_connection_stats() if self.client else {}
        }
