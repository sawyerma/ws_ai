import logging
from fastapi import APIRouter, HTTPException, Response
from db.clickhouse import fetch_bars
from core.services.cache_service import cached, OHLC_TTL

router = APIRouter()
logger = logging.getLogger("trading-api")


@router.get("/ohlc")
@cached("ohlc", ttl=OHLC_TTL)  # Cache für 30 Sekunden
async def get_ohlc(
    symbol: str = "BTCUSDT",  # Default-Symbol für Tests
    market: str = "spot",
    resolution: str = "1s",
    limit: int = 200
):
    """
    Liefert OHLC-Candlestick-Daten für Symbol/Markt aus der Datenbank.
    Standard: 1s-Bars, limit=200 (letzte x Einheiten je resolution).
    Spot: gibt tatsächliche Kerzen zurück.
    Futures (usdtm, coinm): noch keine History → 204 No Content.
    """
    try:
        if market != "spot":
            # noch keine historische OHLC für Futures
            return Response(status_code=204)

        bars = fetch_bars(symbol, market, limit=limit)
        # reverse, damit älteste zuerst
        return [
            {
                "ts":     bar["ts"],
                "open":   float(bar["open"]),
                "high":   float(bar["high"]),
                "low":    float(bar["low"]),
                "close":  float(bar["close"]),
                "volume": float(bar["volume"])
            }
            for bar in reversed(bars)
        ]
    except Exception as e:
        logger.error(f"OHLC-Fehler: {e}")
        raise HTTPException(status_code=500, detail=f"OHLC-Fehler: {e}")
