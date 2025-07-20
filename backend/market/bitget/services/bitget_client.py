import asyncio
import json
import logging
import websockets
import time
from datetime import datetime, timezone
from market.bitget.config import bitget_config, TLS_CONFIG
from market.bitget.utils.adaptive_rate_limiter import AdaptiveRateLimiter
from market.bitget.utils.circuit_breaker import CircuitBreaker
from market.bitget.storage.redis_manager import redis_manager
from market.bitget.api.ws_manager import broadcast_trade_data
from market.bitget.services.auto_remediation import bitget_failover_active

logger = logging.getLogger("bitget-client")

class BitgetWebSocketClient:
    def __init__(self, symbol: str, market_type: str):
        self.symbol = symbol
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
        self.rate_limiter = AdaptiveRateLimiter(
            base_rps=bitget_config.max_rps,
            name=f"ws-{symbol}-{market_type}"
        )
        self.circuit_breaker = CircuitBreaker()
        
    async def start(self):
        if bitget_failover_active:
            logger.info(f"Skipping Bitget for {self.symbol} (failover active)")
            return
            
        self.running = True
        logger.info(f"Starting Bitget client for {self.symbol} ({self.market_type})")
        
        while self.running:
            try:
                await self.circuit_breaker.execute(self._connect_and_listen)
            except Exception as e:
                self.reconnect_count += 1
                logger.error(f"Connection failed ({self.reconnect_count}): {e}")
                await asyncio.sleep(min(2 ** self.reconnect_count, 60))
                
    async def _connect_and_listen(self):
        async with websockets.connect(
            self.ws_url,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10,
            **TLS_CONFIG
        ) as ws:
            logger.info(f"Connected to {self.ws_url} for {self.symbol} ({self.market_type})")
            await self._subscribe(ws)
            
            async for message in ws:
                if not self.running:
                    break
                await self._process_message(message)
                
    async def _subscribe(self, ws):
        start_time = time.time()
        try:
            # Format symbol according to market type
            inst_id = f"{self.symbol}{self.symbol_suffix}"
            
            msg = {
                "op": "subscribe",
                "args": [{
                    "instType": self.inst_type,
                    "channel": "trade", 
                    "instId": inst_id
                }]
            }
            
            await self.rate_limiter.acquire()
            await ws.send(json.dumps(msg))
            
            response_time = time.time() - start_time
            self.rate_limiter.record_success(response_time)
        except Exception as e:
            self.rate_limiter.record_error(type(e).__name__)
            raise
            
    async def _process_message(self, message: str):
        start_time = time.time()
        try:
            msg = json.loads(message)
            if msg.get("event") == "error":
                self.rate_limiter.record_error("api_error")
                logger.error(f"WebSocket error: {msg.get('msg')}")
                return
                
            if msg.get("action") == "update":
                await self._process_trades(msg.get("data", []))
                
            response_time = time.time() - start_time
            self.rate_limiter.record_success(response_time)
        except Exception as e:
            self.rate_limiter.record_error(type(e).__name__)
            logger.error(f"Message processing error: {e}")
            
    async def _process_trades(self, trades: list):
        for trade_data in trades:
            try:
                trade = self._parse_trade(trade_data)
                
                # Store in Redis
                await redis_manager.add_trade(self.symbol, trade, self.market_type)
                
                # Broadcast via WebSocket
                await broadcast_trade_data(self.symbol, trade)
                
            except Exception as e:
                logger.error(f"Trade processing error: {e}")
                
    def _parse_trade(self, trade_data: list) -> dict:
        # Structure: [timestamp, price, size, side]
        ts_ms = trade_data[0]
        price = trade_data[1]
        size = trade_data[2]
        side = trade_data[3]
        
        return {
            "symbol": self.symbol,
            "market_type": self.market_type,
            "price": float(price),
            "size": float(size),
            "side": side.lower(),
            "ts": datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
            "timestamp": ts_ms
        }
        
    async def stop(self):
        self.running = False
        logger.info(f"Stopped Bitget client for {self.symbol} ({self.market_type})")
