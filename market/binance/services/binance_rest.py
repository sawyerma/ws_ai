# market/binance/services/binance_rest.py
import aiohttp
import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional
from market.binance.config import BinanceConfig

logger = logging.getLogger("binance-rest")

class BinanceRestAPI:
    def __init__(self, config: BinanceConfig):
        self.config = config
        self.base_url = "https://fapi.binance.com" if config.is_futures else "https://api.binance.com"
        self.headers = {"X-MBX-APIKEY": config.api_key}
        self.rate_limit = 1200  # Max requests per minute
        self.rate_limit_reset = 0
        self.request_count = 0
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def _rate_limit_check(self):
        current_time = time.time()
        if current_time > self.rate_limit_reset:
            # Reset rate limit counter
            self.request_count = 0
            self.rate_limit_reset = current_time + 60  # Reset in 60 seconds
        
        if self.request_count >= self.rate_limit:
            wait_time = self.rate_limit_reset - current_time
            logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
            self.request_count = 0
            self.rate_limit_reset = time.time() + 60
        
        self.request_count += 1

    async def fetch_historical_trades(self, symbol: str, start_time: datetime, end_time: datetime, limit: int = 1000) -> List[Dict]:
        """Holt historische Trades im UnifiedTrade Format"""
        await self._rate_limit_check()
        
        params = {
            "symbol": symbol.upper(),
            "startTime": int(start_time.timestamp() * 1000),
            "endTime": int(end_time.timestamp() * 1000),
            "limit": min(limit, 1000)  # Binance max limit
        }
        
        endpoint = "/fapi/v1/aggTrades" if self.config.is_futures else "/api/v3/aggTrades"
        
        try:
            async with self.session.get(self.base_url + endpoint, params=params) as response:
                if response.status == 200:
                    trades = await response.json()
                    return [self._parse_trade(trade, symbol) for trade in trades]
                else:
                    error = await response.text()
                    logger.error(f"API error {response.status}: {error}")
                    return []
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return []

    def _parse_trade(self, trade_data: Dict, symbol: str) -> Dict:
        """Konvertiert Binance Trade in UnifiedTrade Format"""
        return {
            "exchange": "binance",
            "symbol": symbol,
            "market": "futures" if self.config.is_futures else "spot",
            "price": float(trade_data['p']),
            "size": float(trade_data['q']),
            "side": "buy" if trade_data['m'] else "sell",
            "timestamp": datetime.utcfromtimestamp(trade_data['T'] / 1000),
            "exchange_id": str(trade_data['a'])
        }

    async def fetch_klines(self, symbol: str, interval: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, limit: int = 500) -> List[Dict]:
        """Holt klines (Candlestick-Daten)"""
        await self._rate_limit_check()
        
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": min(limit, 1000)
        }
        
        if start_time:
            params["startTime"] = int(start_time.timestamp() * 1000)
        if end_time:
            params["endTime"] = int(end_time.timestamp() * 1000)
        
        endpoint = "/fapi/v1/klines" if self.config.is_futures else "/api/v3/klines"
        
        try:
            async with self.session.get(self.base_url + endpoint, params=params) as response:
                if response.status == 200:
                    klines = await response.json()
                    return [self._parse_kline(kline, symbol, interval) for kline in klines]
                else:
                    error = await response.text()
                    logger.error(f"Klines error {response.status}: {error}")
                    return []
        except Exception as e:
            logger.error(f"Klines request failed: {str(e)}")
            return []

    def _parse_kline(self, kline_data: list, symbol: str, interval: str) -> Dict:
        """Konvertiert Binance Kline in Standard-Candle-Format"""
        return {
            "symbol": symbol,
            "market": "futures" if self.config.is_futures else "spot",
            "resolution": interval,
            "open": float(kline_data[1]),
            "high": float(kline_data[2]),
            "low": float(kline_data[3]),
            "close": float(kline_data[4]),
            "volume": float(kline_data[5]),
            "trades": int(kline_data[8]),
            "ts": datetime.utcfromtimestamp(kline_data[0] / 1000),
            "exchange": "binance"
        }

    async def close(self):
        await self.session.close()
        logger.info("REST API session closed")
