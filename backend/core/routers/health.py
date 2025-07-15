import logging
from fastapi import APIRouter

from db.clickhouse import ping
from core.routers.trades import symbol_clients
# from core.routers.market_trades import trade_ws_clients  # optional
from whale.detector import is_detector_alive  # <- NEU (siehe unten)
from whale.settings import fetch_coins  # für aktives Coin-Mapping

router = APIRouter()
logger = logging.getLogger("trading-api")

@router.get("/health")
@router.get("/healthz")
async def health_check():
    """
    Health-Check für API, WebSockets, ClickHouse, Whale-Detection und Coins.
    Standardisiertes Format für Tests.
    """
    from datetime import datetime
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "clickhouse": ping(),
        "websockets_trades": sum(len(s) for s in symbol_clients.values()),
        # "websockets_markettrades": sum(len(s) for s in trade_ws_clients.values()),  # falls vorhanden
        "whale_detector": is_detector_alive(),
        "coins_active": len(fetch_coins(active=1)),
        "ok": True
    }

@router.get("/debugtest")
async def debug_test():
    """
    Testet Logging und Exception-Handling.
    Wirft absichtlich einen Fehler.
    """
    logger.info("Debug-Test gestartet!")
    raise RuntimeError("Dies ist ein absichtlicher Fehler zum Testen der Error-Logs!")
