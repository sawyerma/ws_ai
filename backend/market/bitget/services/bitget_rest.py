import aiohttp
import json
import logging
import hmac
import hashlib
import base64
import time
from market.bitget.config import bitget_config

logger = logging.getLogger("bitget-rest")

class BitgetRestAPI:
    """Vollständige Bitget REST API Integration"""
    
    def __init__(self):
        self.base_url = bitget_config.rest_base_url
        self.api_key = bitget_config.api_key
        self.secret_key = bitget_config.secret_key
        self.passphrase = bitget_config.passphrase
        self.session = aiohttp.ClientSession()
        
    async def _sign_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        timestamp = str(int(time.time() * 1000))
        message = timestamp + method.upper() + endpoint
        
        if params:
            message += json.dumps(params, separators=(',', ':'))
            
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase
        }
    
    async def _get_request(self, endpoint: str, params: dict = None) -> dict:
        headers = await self._sign_request("GET", endpoint, params)
        async with self.session.get(
            f"{self.base_url}{endpoint}", 
            params=params, 
            headers=headers
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def fetch_spot_symbols(self) -> List[Dict]:
        """Spot Symbole - V2 API"""
        return await self._get_request("/api/v2/spot/public/symbols")
        
    async def fetch_futures_symbols(self, product_type: str) -> List[Dict]:
        """Futures Symbole"""
        return await self._get_request("/api/v2/mix/market/contracts", {"productType": product_type})
        
    async def fetch_spot_tickers(self) -> List[Dict]:
        """Spot Ticker"""
        return await self._get_request("/api/v2/spot/market/tickers")
        
    async def fetch_futures_tickers(self, product_type: str) -> List[Dict]:
        """Futures Ticker"""
        return await self._get_request("/api/v2/mix/market/tickers", {"productType": product_type})
        
    async def fetch_spot_orderbook(self, symbol: str, limit: int = 50) -> Dict:
        """Spot Orderbook"""
        return await self._get_request("/api/v2/spot/market/orderbook", {"symbol": symbol, "limit": limit})
        
    async def fetch_futures_orderbook(self, symbol: str, product_type: str, limit: int = 50) -> Dict:
        """Futures Orderbook"""
        return await self._get_request(
            "/api/v2/mix/market/orderbook", 
            {"symbol": symbol, "productType": product_type, "limit": limit}
        )
        
    async def fetch_spot_candles(self, symbol: str, granularity: str, **kwargs) -> List:
        """Spot Kerzen"""
        params = {"symbol": symbol, "granularity": granularity, **kwargs}
        return await self._get_request("/api/v2/spot/market/candles", params)
        
    async def fetch_futures_candles(self, symbol: str, product_type: str, granularity: str, **kwargs) -> List:
        """Futures Kerzen"""
        params = {"symbol": symbol, "productType": product_type, "granularity": granularity, **kwargs}
        return await self._get_request("/api/v2/mix/market/candles", params)
        
    async def close(self):
        await self.session.close()
