import asyncio
import logging
from market.bitget.config import system_config, bitget_config
from market.bitget.services.bitget_rest import BitgetRestAPI

logger = logging.getLogger("symbol-discovery")

class SymbolDiscoveryService:
    """Automatische Symbol-Entdeckung für alle Märkte"""
    
    def __init__(self):
        self.rest_api = BitgetRestAPI()
        self.symbols = {}
        
    async def initialize(self):
        """Initialize and discover all symbols"""
        logger.info("🔍 Starting symbol discovery")
        await self._discover_spot_symbols()
        await self._discover_futures_symbols("USDT-FUTURES")
        logger.info(f"✅ Discovered {len(self.symbols)} symbols")
        
    async def _discover_spot_symbols(self):
        """Discover spot trading symbols"""
        try:
            data = await self.rest_api.fetch_spot_symbols()
            if data.get("code") == "00000":
                for symbol_data in data.get("data", []):
                    if symbol_data.get("status") == "online":
                        self._add_spot_symbol(symbol_data)
        except Exception as e:
            logger.error(f"Spot symbol discovery failed: {e}")
        
    async def _discover_futures_symbols(self, product_type: str):
        """Discover futures trading symbols"""
        try:
            data = await self.rest_api.fetch_futures_symbols(product_type)
            if data.get("code") == "00000":
                for symbol_data in data.get("data", []):
                    if symbol_data.get("status") == "normal":
                        self._add_futures_symbol(symbol_data, "usdtm")
        except Exception as e:
            logger.error(f"Futures symbol discovery failed: {e}")
        
    def _add_spot_symbol(self, symbol_data: dict):
        """Add spot symbol to registry"""
        symbol = symbol_data["symbol"]
        key = f"{symbol}_spot"
        
        self.symbols[key] = {
            "symbol": symbol,
            "market_type": "spot",
            "base_coin": symbol_data.get("baseCoin", ""),
            "quote_coin": symbol_data.get("quoteCoin", ""),
            "status": symbol_data.get("status", ""),
            "min_size": float(symbol_data.get("minTradeAmount", 0)),
            "max_size": float(symbol_data.get("maxTradeAmount", 0)),
            "size_increment": float(symbol_data.get("quantityScale", 0)),
            "price_increment": float(symbol_data.get("priceScale", 0))
        }
        
    def _add_futures_symbol(self, symbol_data: dict, market_type: str):
        """Add futures symbol to registry"""
        symbol = symbol_data["symbol"]
        key = f"{symbol}_{market_type}"
        
        self.symbols[key] = {
            "symbol": symbol,
            "market_type": market_type,
            "base_coin": symbol_data.get("baseCoin", ""),
            "quote_coin": symbol_data.get("quoteCoin", "USDT"),
            "status": symbol_data.get("status", ""),
            "min_size": float(symbol_data.get("minTradeNum", 0)),
            "max_size": float(symbol_data.get("maxTradeNum", 0)),
            "size_increment": float(symbol_data.get("sizeMultiplier", 0)),
            "price_increment": float(symbol_data.get("pricePlace", 0))
        }
        
    async def get_top_symbols_by_volume(self, market_type: str = None, limit: int = 50) -> list:
        """Get top symbols by 24h volume"""
        symbols = list(self.symbols.values())
        if market_type:
            symbols = [s for s in symbols if s["market_type"] == market_type]
            
        # Sort by volume (dummy implementation)
        symbols.sort(key=lambda x: x.get("volume_24h", 0), reverse=True)
        return symbols[:limit]
        
    async def close(self):
        await self.rest_api.close()

# Global instance
symbol_discovery = SymbolDiscoveryService()
