import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, List
from fastapi import APIRouter, Body, HTTPException, Query
from core.routers.exchange_factory import ExchangeFactory
from db.clickhouse import fetch_coin_settings, upsert_coin_setting
from models.trade import MarketType

router = APIRouter(prefix="/settings", tags=["settings"])
logger = logging.getLogger("settings-api")

@router.get("")
async def get_settings(
    exchange: str = Query(None, description="Filter by exchange (binance|bitget)"),
    symbol: str = Query(None, description="Filter by symbol"),
    market: str = Query(None, description="Filter by market type")
):
    try:
        # Validierung
        if market and market not in MarketType.__members__:
            raise HTTPException(400, "Invalid market type")
        
        return fetch_coin_settings(exchange, symbol, market)
    except Exception as e:
        logger.error(f"Settings GET error: {str(e)}")
        raise HTTPException(500, "Failed to retrieve settings")

@router.put("")
async def save_settings(settings: List[Dict[str, Any]] = Body(...)):
    results = []
    for s in settings:
        try:
            exchange = s.get("exchange", "bitget")
            symbol = s["symbol"]
            market = s.get("market", "spot")
            
            # MarketType Validierung
            if market not in MarketType.__members__:
                raise ValueError(f"Invalid market type: {market}")
            
            # Konvertierung der Auflösungen
            db_resolutions = s.get("db_resolutions")
            if isinstance(db_resolutions, int):
                db_resolutions = [db_resolutions]
            
            # Datenbank-Update
            success = upsert_coin_setting(
                exchange=exchange,
                symbol=symbol,
                market=market,
                store_live=int(s.get("store_live", 1)),
                load_history=int(s.get("load_history", 0)),
                history_until=s.get("history_until"),
                favorite=int(s.get("favorite", 0)),
                db_resolutions=db_resolutions or [60],
                chart_resolution=s.get("chart_resolution", "1m")
            )
            
            if not success:
                raise RuntimeError("Database update failed")
            
            # Backfill starten falls benötigt
            if s.get("load_history") and s.get("history_until"):
                try:
                    dt = datetime.fromisoformat(s["history_until"])
                    manager = ExchangeFactory.get_historical_manager(exchange)
                    if manager:
                        asyncio.create_task(manager.history(symbol, dt, market))
                        logger.info(f"Started backfill for {exchange}/{symbol}/{market}")
                except ValueError:
                    logger.error(f"Invalid datetime format: {s['history_until']}")

            results.append({
                "exchange": exchange,
                "symbol": symbol,
                "market": market,
                "ok": True
            })
        except Exception as e:
            logger.error(f"Settings save error: {str(e)}")
            results.append({
                "exchange": s.get("exchange"),
                "symbol": s.get("symbol"),
                "market": s.get("market"),
                "ok": False,
                "error": str(e)
            })

    return results

@router.get("/completeness")
async def get_completeness(symbol: str, until: str):
    """
    Prüft, ob wir bis 'until' historische Daten komplett haben.
    Liefert aktuell immer False.
    """
    return {"symbol": symbol, "complete": False, "until": until}

@router.get("/test")
async def test_settings_connection():
    try:
        test_settings = fetch_coin_settings(exchange="binance")
        return {"status": "success", "settings_found": len(test_settings)}
    except Exception as e:
        logger.critical(f"Settings connection test failed: {str(e)}")
        raise HTTPException(500, "Settings service unavailable")

@router.post("/test-backfill")
async def test_backfill(symbol: str = Body(...), market: str = Body(...)):
    manager = ExchangeFactory.get_historical_manager("binance")
    if manager:
        asyncio.create_task(manager.history(symbol, datetime.utcnow(), market))
        return {"status": "started"}
    return {"status": "no_manager"}
