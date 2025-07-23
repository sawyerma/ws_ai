# market/binance/services/binance_client.py
import aiohttp
import asyncio
import json
import logging
from datetime import datetime
from market.binance.config import BinanceConfig

logger = logging.getLogger("binance-ws")

class BinanceWebSocketClient:
    def __init__(self, symbol: str, market: str, config: BinanceConfig, trade_queue: asyncio.Queue):
        self.symbol = symbol
        self.market = market
        self.config = config
        self.trade_queue = trade_queue
        self.ws_url = self._get_ws_url()
        self.session = None
        self.ws = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1  # Startverzögerung in Sekunden

    def _get_ws_url(self):
        base_url = "wss://fstream.binance.com" if self.market == "futures" else "wss://stream.binance.com:9443"
        stream_type = "aggTrade"  # Komprimierte Trades für bessere Performance
        return f"{base_url}/ws/{self.symbol.lower()}@{stream_type}"

    async def connect(self):
        self.running = True
        self.session = aiohttp.ClientSession()
        
        while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                logger.info(f"Connecting to Binance WS: {self.ws_url}")
                async with self.session.ws_connect(self.ws_url) as websocket:
                    self.ws = websocket
                    self.reconnect_attempts = 0
                    
                    async for msg in websocket:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await self._process_message(msg.data)
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
            finally:
                if self.running:
                    await self._handle_reconnect()
        
        logger.warning("WebSocket connection terminated")

    async def _process_message(self, data: str):
        try:
            trade_data = json.loads(data)
            trade = {
                "exchange": "binance",
                "symbol": self.symbol,
                "market": self.market,
                "price": float(trade_data['p']),
                "size": float(trade_data['q']),
                "side": "buy" if trade_data['m'] else "sell",
                "timestamp": datetime.utcfromtimestamp(trade_data['T'] / 1000),
                "exchange_id": str(trade_data['a'])
            }
            await self.trade_queue.put(trade)
        except Exception as e:
            logger.error(f"Error processing trade: {str(e)}")

    async def _handle_reconnect(self):
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            delay = min(self.reconnect_delay * 2 ** self.reconnect_attempts, 30)
            logger.warning(f"Reconnecting attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} in {delay}s")
            await asyncio.sleep(delay)
        else:
            logger.critical("Max reconnect attempts reached")
            self.running = False

    async def disconnect(self):
        self.running = False
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
        logger.info("WebSocket disconnected")
