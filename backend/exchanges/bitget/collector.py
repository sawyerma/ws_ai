import asyncio
import json
import traceback
import logging
from datetime import datetime, timezone
import websockets

logger = logging.getLogger("bitget-collector")

class BitgetCollector:
    """
    Holt Live-Trades für ein Symbol & Markt (Spot/Futures) von Bitget per WebSocket
    und legt sie in eine asyncio.Queue für das Backend.
    """
    def __init__(self, symbol: str, market: str, queue: asyncio.Queue):
        self.symbol = symbol
        self.market = market      # 'spot', 'umcbl', 'dmcbl', ...
        self._queue = queue
        self._ws_url = self._get_ws_url(market)
        self._instType = self._get_inst_type(market)
        self._channel = "trade"
        self._reconnect_delay = 5
        self._running = True

    def _get_ws_url(self, market):
        if market == "spot":
            return "wss://ws.bitget.com/spot/v1/stream"
        else:
            return "wss://ws.bitget.com/mix/v1/stream"

    def _get_inst_type(self, market):
        return "SP" if market == "spot" else "MC"

    async def start(self):
        while self._running:
            try:
                async with websockets.connect(self._ws_url, ping_interval=15, ping_timeout=10) as ws:
                    inst_id = self.symbol if self.market == "spot" else f"{self.symbol}_{self.market.upper()}"
                    sub_msg = {
                        "op": "subscribe",
                        "args": [{
                            "instType": self._instType,
                            "channel": self._channel,
                            "instId": inst_id
                        }]
                    }
                    await ws.send(json.dumps(sub_msg))
                    logger.info(f"[{datetime.utcnow().isoformat()}] [Collector:{self.symbol}|{self.market}] Subscribed: {sub_msg}")

                    async for message in ws:
                        if not self._running:
                            break
                        try:
                            msg = json.loads(message)
                            if msg.get("action") != "update":
                                continue
                            for entry in msg.get("data", []):
                                ts_ms, price, size, side = entry
                                dt = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc)
                                trade = {
                                    "symbol": self.symbol,
                                    "market": self.market,
                                    "price": float(price),
                                    "size": float(size),
                                    "side": side,
                                    "ts": dt.isoformat()
                                }
                                await self._queue.put(trade)
                        except Exception:
                            logger.error(f"[{datetime.utcnow().isoformat()}] [Collector:{self.symbol}|{self.market}] Parse error:\n{traceback.format_exc()}")

            except Exception as e:
                logger.error(f"[{datetime.utcnow().isoformat()}] [Collector:{self.symbol}|{self.market}] Connection error: {e}\n{traceback.format_exc()}")
                await asyncio.sleep(self._reconnect_delay)

    def stop(self):
        self._running = False
