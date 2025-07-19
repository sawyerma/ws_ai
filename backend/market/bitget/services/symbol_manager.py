import logging
from market.bitget.config import system_config
from market.bitget.services.symbol_discovery import symbol_discovery

logger = logging.getLogger("symbol-manager")

class SymbolManager:
    """Manages active symbols for trading"""
    
    def __init__(self):
        self.active_symbols = {}
        
    async def initialize_symbols(self):
        """Initialize symbols from discovery service"""
        await symbol_discovery.initialize()
        
        # Get top symbols by volume for selected markets
        selected_symbols = set()
        
        for market_type in system_config.market_types:
            top_symbols = await symbol_discovery.get_top_symbols_by_volume(
                market_type, 
                system_config.max_symbols_per_market
            )
            
            for symbol_info in top_symbols:
                if symbol_info.get("volume_24h", 0) >= system_config.min_volume_24h:
                    selected_symbols.add(symbol_info["symbol"])
        
        # Update system config
        system_config.symbols = list(selected_symbols)
        logger.info(f"✅ Selected {len(system_config.symbols)} symbols for trading")
        
        # Activate symbols
        for symbol in system_config.symbols:
            for market_type in system_config.market_types:
                await self.activate_symbol(symbol, market_type)
        
    async def activate_symbol(self, symbol: str, market_type: str):
        """Activate a symbol for trading"""
        key = f"{symbol}_{market_type}"
        self.active_symbols[key] = True
        logger.info(f"✅ Activated {symbol} ({market_type})")
        
    def is_symbol_active(self, symbol: str, market_type: str) -> bool:
        """Check if symbol is active"""
        key = f"{symbol}_{market_type}"
        return key in self.active_symbols
        
    def get_active_symbols(self) -> list:
        """Get list of active symbols"""
        return list(set(symbol.split('_')[0] for symbol in self.active_symbols.keys()))

# Global instance  
symbol_manager = SymbolManager()
