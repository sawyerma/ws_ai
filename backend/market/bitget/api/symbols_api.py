from fastapi import APIRouter, Query
from market.bitget.services.symbol_discovery import symbol_discovery

router = APIRouter()

@router.get("/symbols/all")
async def get_all_symbols():
    """Get all discovered symbols"""
    return {
        "total_symbols": len(symbol_discovery.symbols),
        "symbols": symbol_discovery.symbols
    }

@router.get("/symbols/top")
async def get_top_symbols(
    market_type: str = Query(None, description="Market type (spot, usdtm, etc.)"),
    limit: int = Query(50, description="Number of symbols to return")
):
    """Get top symbols by volume"""
    symbols = await symbol_discovery.get_top_symbols_by_volume(market_type, limit)
    return {
        "market_type": market_type or "all",
        "count": len(symbols),
        "symbols": symbols
    }

@router.get("/symbols/{symbol}/info")
async def get_symbol_info(
    symbol: str, 
    market_type: str = Query(..., description="Market type")
):
    """Get detailed info for a symbol"""
    key = f"{symbol}_{market_type}"
    symbol_info = symbol_discovery.symbols.get(key)
    if not symbol_info:
        return {"error": "Symbol not found"}
    return symbol_info
