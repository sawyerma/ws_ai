import asyncio
import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Set, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Body, HTTPException, Query

from db.clickhouse import insert_trade, fetch_trades
from exchanges.bitget.collector import BitgetCollector
from exchanges.bitget.backfill import BitgetBackfill
from core.routers.symbols import get_symbols  # Optional für Routing-Integration
from core.services.cache_service import cached, DEFAULT_TTL

router = APIRouter()
logger = logging.getLogger("trading-api")

# Globale Maps für WS-Clients und Collector/Queues
symbol_clients: Dict[str, Set[WebSocket]] = {}
collectors: Dict[str, BitgetCollector] = {}
queues: Dict[str, asyncio.Queue] = {}

# ----- Gemeinsamer WebSocket-Handler -----
async def websocket_handler(ws: WebSocket, symbol: str, market: str):
    await ws.accept()
    symbol_key = f"{symbol}_{market}"
    symbol_clients.setdefault(symbol_key, set()).add(ws)
    if symbol_key not in queues:
        queues[symbol_key] = asyncio.Queue()
        collector = BitgetCollector(symbol, market, queues[symbol_key])
        collectors[symbol_key] = collector
        asyncio.create_task(collector.start())
        logger.info(f"[Collector] Started for {symbol}/{market}")

    # Sende initial letzten N Trades
    try:
        trades = fetch_trades(symbol, market, limit=30)
        for trade in reversed(trades):
            await ws.send_text(json.dumps({
                "type": "trade",
                **trade
            }))
    except Exception as e:
        logger.error(f"Trade-Snapshot Fehler: {e}")

    try:
        while True:
            trade = await queues[symbol_key].get()
            await ws.send_text(json.dumps({
                "type": "trade",
                **trade
            }))
    except WebSocketDisconnect:
        symbol_clients[symbol_key].discard(ws)
        logger.info(f"WebSocket getrennt: {symbol}/{market}")

# ----- Neue & Alte URL-Varianten -----

# Variante 1: /ws/BTCUSDT (Frontend-ALT, implizit market="spot")
@router.websocket("/ws/{symbol}")
async def websocket_legacy(ws: WebSocket, symbol: str):
    await websocket_handler(ws, symbol, "spot")

# Variante 2: /ws/BTCUSDT/spot/trades (Frontend-ALT, Standard)
@router.websocket("/ws/{symbol}/{market}/trades")
async def websocket_legacy_trades(ws: WebSocket, symbol: str, market: str):
    await websocket_handler(ws, symbol, market)

# Variante 3: /ws/BTCUSDT/spot (NEU, Backend Default)
@router.websocket("/ws/{symbol}/{market}")
async def websocket_trades(ws: WebSocket, symbol: str, market: str):
    await websocket_handler(ws, symbol, market)

# ----- Trades Publish-Endpoint -----
@router.post("/publish")
async def publish(trade: Dict[str, Any] = Body(...)):
    ts = trade.get("ts")
    dt = datetime.fromisoformat(ts.rstrip("Z")) if ts else datetime.now(timezone.utc)
    insert_trade(
        trade["symbol"],
        trade.get("market", "spot"),
        float(trade["price"]),
        float(trade["size"]),
        trade.get("side", ""),
        dt.isoformat()
    )
    # Push für alle WS-Clients (Broadcast)
    symbol_key = f'{trade["symbol"]}_{trade.get("market", "spot")}'
    for ws in symbol_clients.get(symbol_key, set()):
        try:
            asyncio.create_task(ws.send_text(json.dumps({
                "type": "trade",
                **trade
            })))
        except Exception as e:
            logger.error(f"WS-Broadcast Error: {e}")
            symbol_clients[symbol_key].discard(ws)
    return {"ok": True}

# ----- Trades GET-Endpoint für Curl & Frontend -----
@router.get("/trades")
@cached("trades", ttl=5)  # Cache für 5 Sekunden (sehr kurz für Live-Daten)
async def get_trades(
    symbol: str = Query("BTCUSDT"),  # Default-Symbol statt required
    market: str = Query("spot"),
    limit: int = Query(100)
):
    try:
        trades = fetch_trades(symbol, market, limit=limit)
        return trades
    except Exception as e:
        logger.error(f"Fetch trades error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Fetch trades error")

# ----- Backfill (direkt aus Settings oder als Helper für Tasks) -----
@router.post("/backfill")
async def backfill_endpoint(
    symbol: str = Body(...),
    until: str = Body(...),
    granularity: str = Body("1s"),
    limit: int = Body(200)
):
    try:
        until_dt = datetime.fromisoformat(until.rstrip('Z')).replace(tzinfo=timezone.utc)
        manager = BitgetBackfill()
        await manager.history(symbol, until_dt, granularity, limit)
        await manager.close()
        return {"ok": True}
    except Exception as e:
        logger.error(f"Backfill Fehler: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
