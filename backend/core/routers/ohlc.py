import logging
from fastapi import APIRouter, Query, HTTPException
from db.clickhouse import fetch_bars
from core.routers.exchange_factory import ExchangeFactory
from models.trade import MarketType
from core.services.cache_service import cached, OHLC_TTL

router = APIRouter()
logger = logging.getLogger("ohlc-api")

# Mapping von Auflösungs-Strings zu Sekunden
RESOLUTION_MAP = {
    "1s": 1, "1m": 60, "5m": 300, 
    "15m": 900, "1h": 3600, "4h": 14400,
    "1d": 86400
}

@router.get("/ohlc")
@cached("ohlc", ttl=OHLC_TTL)  # Cache für 30 Sekunden
async def get_ohlc(
    exchange: str = Query("bitget", description="Exchange name (binance|bitget)"),
    symbol: str = Query("BTCUSDT", description="Trading symbol"),
    market: str = Query("spot", description="Market type (spot|usdtm|coinm|usdcm)"),
    resolution: str = Query("1m", description="Candle resolution (1s, 1m, 5m, etc.)"),
    limit: int = Query(200, description="Number of candles to retrieve", gt=0, le=1000)
):
    """
    Liefert OHLC-Candlestick-Daten für Exchange/Symbol/Markt aus der Datenbank.
    Unterstützt alle Exchanges (Binance, Bitget) und alle Markttypen.
    """
    try:
        # Validate market type
        if market not in MarketType.__members__:
            raise HTTPException(400, f"Invalid market type. Supported: {list(MarketType.__members__.keys())}")
        
        # Convert resolution to seconds
        resolution_sec = RESOLUTION_MAP.get(resolution.lower())
        if not resolution_sec:
            raise HTTPException(400, f"Unsupported resolution. Supported: {list(RESOLUTION_MAP.keys())}")
        
        # Fetch from ClickHouse
        bars = fetch_bars(
            exchange=exchange,
            symbol=symbol,
            market=market,
            resolution=resolution_sec,
            limit=limit
        )
        
        # Format response - reverse für chronologische Reihenfolge (älteste zuerst)
        return [{
            "ts": bar["ts"],
            "open": float(bar["open"]),
            "high": float(bar["high"]),
            "low": float(bar["low"]),
            "close": float(bar["close"]),
            "volume": float(bar["volume"]),
            "trades": bar.get("trades", 0)
        } for bar in reversed(bars)]
    
    except HTTPException:
        raise  # Re-raise validation errors
    
    except Exception as e:
        logger.error(f"OHLC error for {exchange}/{symbol}/{market}: {e}", exc_info=True)
        raise HTTPException(500, "Failed to retrieve OHLC data")

@router.get("/ohlc/test")
async def test_ohlc_connection():
    """Test-Endpoint für OHLC-Service Verfügbarkeit"""
    try:
        # Teste Verbindung zur ersten verfügbaren Tabelle
        test_bars = fetch_bars(
            exchange="bitget",
            symbol="BTCUSDT",
            market="spot",
            resolution=60,
            limit=1
        )
        return {"status": "success", "bars_found": len(test_bars)}
    except Exception as e:
        logger.critical(f"OHLC connection test failed: {str(e)}")
        raise HTTPException(500, "OHLC service unavailable")
