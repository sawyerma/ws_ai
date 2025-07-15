import logging
import asyncio
from typing import Any, Dict, List
from datetime import datetime

from fastapi import APIRouter, Body, HTTPException

from db.clickhouse import fetch_coin_settings, upsert_coin_setting
from exchanges.bitget.backfill import BitgetBackfill

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
)

logger = logging.getLogger("trading-api")


@router.get("")
async def get_settings():
    """
    Gibt alle gespeicherten Coin-Einstellungen (Datenbank) zurück.
    """
    try:
        return fetch_coin_settings()
    except Exception as e:
        logger.error(f"Settings-GET-Error: {e}")
        raise HTTPException(status_code=500, detail="Settings-Fehler")


@router.put("")
async def save_settings(settings: List[Dict[str, Any]] = Body(...)):
    """
    Speichert/aktualisiert Einstellungen für Coins (store_live, load_history, ...).
    Optional: Startet Backfill, wenn load_history + history_until gesetzt.
    """
    results = []
    for s in settings:
        try:
            dt = datetime.fromisoformat(s["history_until"]) if s.get("history_until") else None
            upsert_coin_setting(
                symbol=s["symbol"],
                market=s.get("market", "spot"),
                store_live=int(s.get("store_live", 1)),
                load_history=int(s.get("load_history", 0)),
                history_until=s.get("history_until"),
                favorite=int(s.get("favorite", 0)),
                db_resolution=int(s.get("db_resolution", 1)),
                chart_resolution=s.get("chart_resolution", "1s"),
            )
            # falls History geladen werden soll, Backfill im Hintergrund starten
            if s.get("load_history") and dt:
                manager = BitgetBackfill()
                asyncio.create_task(manager.history(s["symbol"], dt))

            results.append({"symbol": s["symbol"], "ok": True})
        except Exception as e:
            logger.error(f"Settings-Save-Error for symbol {s.get('symbol')}: {e}")
            results.append({"symbol": s.get("symbol"), "ok": False, "error": str(e)})

    return results


@router.get("/completeness")
async def get_completeness(symbol: str, until: str):
    """
    Prüft, ob wir bis 'until' historische Daten komplett haben.
    Liefert aktuell immer False.
    """
    return {"symbol": symbol, "complete": False, "until": until}
