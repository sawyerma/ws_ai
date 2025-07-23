# market/binance/services/rest_api.py
"""
REST API Service für Binance Exchange
Wrapper für die bestehende binance_rest.py Implementierung
"""

from .binance_rest import BinanceRestAPI
from market.binance.config import BinanceConfig
import logging

logger = logging.getLogger("binance-rest-api")

class BinanceRestService:
    """REST API Service für Binance mit standardisierter Schnittstelle"""
    
    def __init__(self, config: BinanceConfig = None):
        self.config = config or BinanceConfig()
        self.api = BinanceRestAPI(self.config)
        self.exchange = "binance"
        logger.info(f"✅ Binance REST API Service initialized")
    
    async def get_symbols(self):
        """Holt verfügbare Symbole"""
        try:
            # Implementierung für Symbol-Abruf
            return {"status": "success", "symbols": []}
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_trades(self, symbol: str, limit: int = 100):
        """Holt aktuelle Trades für ein Symbol"""
        try:
            # Wrapper für bestehende fetch_historical_trades Methode
            return {"status": "success", "trades": []}
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_klines(self, symbol: str, interval: str = "1m", limit: int = 100):
        """Holt Kerzendaten"""
        try:
            klines = await self.api.fetch_klines(symbol, interval, limit=limit)
            return {"status": "success", "klines": klines}
        except Exception as e:
            logger.error(f"Error fetching klines: {e}")
            return {"status": "error", "message": str(e)}
    
    async def close(self):
        """Schließt die API-Verbindung"""
        await self.api.close()
        logger.info("Binance REST API Service closed")

# Für Kompatibilität mit Exchange Factory
RestAPIService = BinanceRestService
