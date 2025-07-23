import logging
from fastapi import APIRouter, Query, HTTPException
from core.routers.exchange_factory import ExchangeFactory
from core.services.cache_service import cached, SYMBOLS_TTL

router = APIRouter()
logger = logging.getLogger("symbols-api")

@router.get("/symbols")
@cached("symbols", ttl=SYMBOLS_TTL)
async def get_symbols(
    exchange: str = Query("bitget", description="Exchange name (binance|bitget)"),
    market: str = Query(None, description="Filter by market type (spot|futures)")
):
    try:
        # Holen der REST API Instanz aus der Factory
        api = ExchangeFactory.get_rest_api(exchange)
        if not api:
            raise HTTPException(400, "Exchange not supported")
        
        # Abrufen der Symbole mit optionalem Marktfilter
        symbols = await api.fetch_symbols(market_filter=market)
        
        return {
            "exchange": exchange,
            "symbols": symbols,
            "count": len(symbols)
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Symbols API error for {exchange}: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to retrieve symbols: {str(e)}")

@router.get("/ticker")
@cached("ticker", ttl=10)  # Kürzeres TTL für Ticker-Daten
async def get_ticker(
    exchange: str = Query("bitget", description="Exchange name (binance|bitget)"),
    symbol: str = Query(None, description="Specific symbol to retrieve"),
    market: str = Query(None, description="Filter by market type (spot|futures)")
):
    try:
        api = ExchangeFactory.get_rest_api(exchange)
        if not api:
            raise HTTPException(400, "Exchange not supported")
        
        # Abrufen der Ticker-Daten
        tickers = await api.fetch_tickers(market_filter=market)
        
        # Optional: Filter nach spezifischem Symbol
        if symbol:
            tickers = [t for t in tickers if t['symbol'] == symbol]
            if not tickers:
                raise HTTPException(404, "Symbol not found")
        
        return {
            "exchange": exchange,
            "tickers": tickers,
            "count": len(tickers)
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Ticker API error for {exchange}: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to retrieve ticker data: {str(e)}")

@router.get("/symbols/test")
async def test_symbols_connection():
    try:
        symbols = await get_symbols(exchange="binance")
        return {"status": "success", "symbol_count": symbols["count"]}
    except Exception as e:
        logger.critical(f"Symbols connection test failed: {str(e)}")
        raise HTTPException(500, "Symbols service unavailable")

@router.get("/ticker/test")
async def test_ticker_connection():
    try:
        tickers = await get_ticker(exchange="bitget", symbol="BTCUSDT")
        return {"status": "success", "ticker": tickers["tickers"][0] if tickers["tickers"] else None}
    except Exception as e:
        logger.critical(f"Ticker connection test failed: {str(e)}")
        raise HTTPException(500, "Ticker service unavailable")
