# market/bitget/services/rest_api.py
"""
REST API Service für Bitget Exchange
"""

import aiohttp
import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger("bitget-rest-api")

class BitgetRestService:
    """REST API Service für Bitget mit standardisierter Schnittstelle"""
    
    def __init__(self, config=None):
        self.config = config
        self.base_url = "https://api.bitget.com"
        self.headers = {"Content-Type": "application/json"}
        self.exchange = "bitget"
        self.session = None
        logger.info(f"✅ Bitget REST API Service initialized")
    
    async def _get_session(self):
        """Lazy session initialization"""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
    
    async def get_symbols(self):
        """Holt verfügbare Symbole"""
        try:
            session = await self._get_session()
            endpoint = "/api/spot/v1/public/products"
            
            async with session.get(self.base_url + endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    symbols = []
                    if data.get("code") == "00000" and "data" in data:
                        for item in data["data"]:
                            symbols.append({
                                "symbol": item.get("symbol"),
                                "base": item.get("baseCoin"),
                                "quote": item.get("quoteCoin"),
                                "status": item.get("status")
                            })
                    return {"status": "success", "symbols": symbols}
                else:
                    error = await response.text()
                    logger.error(f"API error {response.status}: {error}")
                    return {"status": "error", "message": error}
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_trades(self, symbol: str, limit: int = 100):
        """Holt aktuelle Trades für ein Symbol"""
        try:
            session = await self._get_session()
            endpoint = "/api/spot/v1/market/fills"
            params = {
                "symbol": symbol.upper(),
                "limit": min(limit, 100)  # Bitget max limit
            }
            
            async with session.get(self.base_url + endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    trades = []
                    if data.get("code") == "00000" and "data" in data:
                        for trade in data["data"]:
                            trades.append({
                                "price": float(trade.get("price", 0)),
                                "size": float(trade.get("size", 0)),
                                "side": trade.get("side", "unknown"),
                                "timestamp": trade.get("ts", ""),
                                "symbol": symbol
                            })
                    return {"status": "success", "trades": trades}
                else:
                    error = await response.text()
                    logger.error(f"API error {response.status}: {error}")
                    return {"status": "error", "message": error}
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_klines(self, symbol: str, interval: str = "1m", limit: int = 100):
        """Holt Kerzendaten"""
        try:
            session = await self._get_session()
            endpoint = "/api/spot/v1/market/candles"
            params = {
                "symbol": symbol.upper(),
                "period": interval,
                "limit": min(limit, 200)  # Bitget max limit
            }
            
            async with session.get(self.base_url + endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    klines = []
                    if data.get("code") == "00000" and "data" in data:
                        for kline in data["data"]:
                            klines.append({
                                "symbol": symbol,
                                "market": "spot",
                                "resolution": interval,
                                "open": float(kline[1]),
                                "high": float(kline[2]),
                                "low": float(kline[3]),
                                "close": float(kline[4]),
                                "volume": float(kline[5]),
                                "ts": datetime.utcfromtimestamp(int(kline[0]) / 1000),
                                "exchange": "bitget"
                            })
                    return {"status": "success", "klines": klines}
                else:
                    error = await response.text()
                    logger.error(f"API error {response.status}: {error}")
                    return {"status": "error", "message": error}
        except Exception as e:
            logger.error(f"Error fetching klines: {e}")
            return {"status": "error", "message": str(e)}
    
    async def close(self):
        """Schließt die API-Verbindung"""
        if self.session:
            await self.session.close()
        logger.info("Bitget REST API Service closed")

# Für Kompatibilität mit Exchange Factory
RestAPIService = BitgetRestService
