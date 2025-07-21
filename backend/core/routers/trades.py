import asyncio
import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Set, Any, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Body, HTTPException, Query
from market.bitget.collector import BitgetCollector
from market.bitget.historical import BitgetBackfill
from market.bitget.storage.redis_manager import redis_manager

router = APIRouter()
logger = logging.getLogger("trades-api")

# Globale State-Handling
symbol_clients: Dict[str, Set[WebSocket]] = {}
collectors: Dict[str, BitgetCollector] = {}
queues: Dict[str, asyncio.Queue] = {}

async def websocket_handler(ws: WebSocket, symbol: str, market: str):
    await ws.accept()
    symbol_key = f"{symbol}_{market}"
    
    # Client registrieren
    if symbol_key not in symbol_clients:
        symbol_clients[symbol_key] = set()
    symbol_clients[symbol_key].add(ws)

    # Collector-Instanz starten (falls nicht existiert)
    if symbol_key not in queues:
        queues[symbol_key] = asyncio.Queue()
        collector = BitgetCollector(symbol, market)
        collectors[symbol_key] = collector
        asyncio.create_task(collector.start())
        logger.info(f"Collector started for {symbol_key}")

    # Letzte Trades senden
    try:
        trades: List[Dict] = await redis_manager.get_recent_trades(symbol, market, 30)
        for trade in reversed(trades):
            await ws.send_text(json.dumps({"type": "trade", **trade}))
    except Exception as e:
        logger.error(f"Trade snapshot failed: {str(e)}")

    # Live-Trades verarbeiten
    try:
        while True:
            # Hier würden normalerweise Nachrichten aus der Queue kommen
            # Für dieses Beispiel verwenden wir einen Platzhalter
            await asyncio.sleep(1)
            trade = {
                "symbol": symbol,
                "market": market,
                "price": 50000.0,
                "size": 0.1,
                "side": "buy",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await ws.send_text(json.dumps({"type": "trade", **trade}))
    except WebSocketDisconnect:
        symbol_clients[symbol_key].remove(ws)
        logger.info(f"WebSocket disconnected: {symbol_key}")

        # Collector stoppen wenn keine Clients mehr
        if not symbol_clients[symbol_key]:
            await collectors[symbol_key].stop()
            del collectors[symbol_key]
            del queues[symbol_key]
            del symbol_clients[symbol_key]

# WebSocket-Endpoints
@router.websocket("/ws/{symbol}")
async def websocket_legacy(ws: WebSocket, symbol: str):
    await websocket_handler(ws, symbol, "spot")

@router.websocket("/ws/{symbol}/{market}/trades")
async def websocket_legacy_trades(ws: WebSocket, symbol: str, market: str):
    await websocket_handler(ws, symbol, market)

@router.websocket("/ws/{symbol}/{market}")
async def websocket_trades(ws: WebSocket, symbol: str, market: str):
    await websocket_handler(ws, symbol, market)

# Publish-Endpoint
@router.post("/publish")
async def publish(trade: Dict[str, Any] = Body(...)):
    try:
        # Datenvalidierung
        ts = trade.get("ts", "")
        dt = datetime.fromisoformat(ts.rstrip("Z")) if ts else datetime.now(timezone.utc)
        
        # In Redis speichern
        await redis_manager.add_trade(
            trade["symbol"],
            trade.get("market", "spot"),
            float(trade["price"]),
            float(trade["size"]),
            trade.get("side", "unknown"),
            dt
        )
        
        # Broadcast an Subscriber
        symbol_key = f'{trade["symbol"]}_{trade.get("market", "spot")}'
        for ws in set(symbol_clients.get(symbol_key, [])):
            try:
                await ws.send_text(json.dumps({"type": "trade", **trade}))
            except (WebSocketDisconnect, RuntimeError):
                symbol_clients[symbol_key].discard(ws)
                
        return {"status": "success"}
    
    except KeyError as e:
        raise HTTPException(400, f"Missing field: {str(e)}")

# GET-Endpoint
@router.get("/trades")
async def get_trades(
    symbol: str = Query("BTCUSDT"),
    market: str = Query("spot"),
    limit: int = Query(100, gt=0, le=1000)
) -> List[Dict]:
    return await redis_manager.get_recent_trades(symbol, market, limit)

# Backfill-Endpoint
@router.post("/backfill")
async def backfill_endpoint(
    symbol: str = Body(...),
    until: str = Body(...),
    granularity: str = Body("1min"),
    limit: int = Body(200)
):
    try:
        until_dt = datetime.fromisoformat(until.rstrip('Z')).replace(tzinfo=timezone.utc)
        async with BitgetBackfill() as manager:
            await manager.history(symbol, until_dt, granularity, limit)
        return {"status": "backfill completed"}
    
    except ValueError as e:
        raise HTTPException(400, f"Invalid datetime format: {str(e)}")