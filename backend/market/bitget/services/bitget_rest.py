import aiohttp
import json
import logging
import hmac
import hashlib
import base64
import time
import asyncio
from typing import Dict, List, Optional
from market.bitget.config import bitget_config
from market.bitget.utils.adaptive_rate_limiter import AdaptiveRateLimiter

logger = logging.getLogger("bitget-rest")

class BitgetRestAPI:
    """Dynamische Bitget REST API Integration mit Free/Premium Support"""
    
    def __init__(self):
        self.base_url = bitget_config.rest_base_url
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = AdaptiveRateLimiter("bitget-rest")
        self._current_config_hash = self._get_config_hash()
        
    def _get_config_hash(self) -> str:
        """Erzeugt Hash der aktuellen Konfiguration"""
        config_str = f"{bitget_config.api_key}{bitget_config.secret_key}{bitget_config.passphrase}"
        return hashlib.md5(config_str.encode()).hexdigest()
    
    async def _ensure_session(self):
        """Stellt sicher, dass eine gültige Session existiert"""
        config_hash = self._get_config_hash()
        
        # Session neu erstellen wenn Konfiguration geändert wurde
        if (self._session is None or 
            self._session.closed or 
            config_hash != self._current_config_hash):
            
            if self._session and not self._session.closed:
                await self._session.close()
            
            # Timeout basierend auf Account-Typ
            timeout = aiohttp.ClientTimeout(total=60 if bitget_config.is_premium else 30)
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'User-Agent': 'Bitget-Trading-System/1.0',
                    'Content-Type': 'application/json'
                }
            )
            
            self._current_config_hash = config_hash
            
            # Rate Limiter aktualisieren
            self._rate_limiter.update_base_rps(bitget_config.effective_max_rps)
            
            logger.info(f"✅ Session {'renewed' if config_hash != self._current_config_hash else 'created'} "
                       f"- Premium: {bitget_config.is_premium}, RPS: {bitget_config.effective_max_rps}")
    
    @property
    def is_premium(self) -> bool:
        """Check if premium features are available"""
        return bitget_config.is_premium
    
    @property
    def requires_auth(self) -> bool:
        """Check if API key authentication is available"""
        return (bitget_config.api_key != "PUBLIC_ACCESS" and 
                bitget_config.secret_key and 
                bitget_config.passphrase)
        
    async def _sign_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """Erstellt signierte Headers für authentifizierte Requests"""
        if not self.requires_auth:
            return {}
        
        timestamp = str(int(time.time() * 1000))
        message = timestamp + method.upper() + endpoint
        
        if params:
            message += json.dumps(params, separators=(',', ':'))
            
        signature = base64.b64encode(
            hmac.new(
                bitget_config.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return {
            "ACCESS-KEY": bitget_config.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": bitget_config.passphrase
        }
    
    async def _get_request(self, endpoint: str, params: dict = None, require_auth: bool = False) -> dict:
        """Führt GET Request mit automatischer Session-Verwaltung und Rate Limiting aus"""
        await self._ensure_session()
        
        # Rate limiting anwenden
        await self._rate_limiter.acquire()
        
        try:
            headers = {}
            
            # Authentifizierung nur wenn erforderlich und verfügbar
            if require_auth and self.requires_auth:
                auth_headers = await self._sign_request("GET", endpoint, params)
                headers.update(auth_headers)
            elif require_auth and not self.requires_auth:
                raise ValueError(f"Authentication required for {endpoint} but no API credentials configured")
            
            async with self._session.get(
                f"{self.base_url}{endpoint}", 
                params=params, 
                headers=headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Erfolg an Rate Limiter melden
                self._rate_limiter.report_success()
                
                return data
                
        except Exception as e:
            # Fehler an Rate Limiter melden
            self._rate_limiter.report_error(e)
            raise
    
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
        """Schließt die Session ordnungsgemäß"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("✅ BitgetRestAPI session closed")
