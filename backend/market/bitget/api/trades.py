import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Set, Any, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Body, HTTPException, Query
from market.bitget.collector import BitgetCollector
from market.bitget.historical import BitgetBackfill
from market.bitget.storage.redis_manager import redis_manager

router = APIRouter()
logger = logging.getLogger("trades-api")

# Hochleistungs-Globalzustand
symbol_clients: Dict[str, Set[WebSocket]] = {}
collectors: Dict[str, BitgetCollector] = {}
data_queues: Dict[str, asyncio.Queue] = {}
broadcast_tasks: Dict[str, asyncio.Task] = {}

async def websocket_handler(ws: WebSocket, symbol: str, market: str):
    """WebSocket-Handler für Echtzeit-Trades"""
    await ws.accept()
    symbol_key = f"{symbol}_{market}"
    
    # Client registrieren
    if symbol_key not in symbol_clients:
        symbol_clients[symbol_key] = set()
    symbol_clients[symbol_key].add(ws)

    # Collector-System initialisieren
    if symbol_key not in collectors:
        # Hochleistungs-Queue für Daten
        queue = asyncio.Queue(maxsize=1000)
        data_queues[symbol_key] = queue
        
        # Collector starten
        collector = BitgetCollector(symbol, market, queue)
        collectors[symbol_key] = collector
        await collector.start()
        
        # Broadcast-Task starten
        broadcast_tasks[symbol_key] = asyncio.create_task(
            broadcast_task(symbol_key, queue)
        
        logger.info(f"🚀 Collector system started for {symbol_key}")

    # Snapshot der letzten Trades senden
    try:
        trades = await redis_manager.get_recent_trades(symbol, market, 30)
        for trade in trades:
            await ws.send_text(json.dumps({"type": "trade", "data": trade}))
    except Exception as e:
        logger.error(f"Snapshot failed: {e}")

    # Live-Daten empfangen
    try:
        while True:
            # Ping/Pong für Verbindungsüberwachung
            await asyncio.sleep(30)
            await ws.send_json({"type": "ping", "ts": int(time.time() * 1000)})
    except WebSocketDisconnect:
        symbol_clients[symbol_key].discard(ws)
        logger.info(f"🔌 WebSocket disconnected: {symbol_key}")

        # Ressourcen bereinigen wenn keine Clients mehr
        if not symbol_clients[symbol_key]:
            await cleanup_symbol(symbol_key)

async def broadcast_task(symbol_key: str, queue: asyncio.Queue):
    """Broadcast-Task für hohen Durchsatz"""
    try:
        while True:
            trade = await queue.get()
            await broadcast_trade(symbol_key, trade)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Broadcast task failed for {symbol_key}: {e}")

async def broadcast_trade(symbol_key: str, trade: dict):
    """Sendet Trade an alle verbundenen Clients"""
    clients = symbol_clients.get(symbol_key, set()).copy()
    if not clients:
        return
        
    message = json.dumps({"type": "trade", "data": trade})
    tasks = [ws.send_text(message) for ws in clients]
    await asyncio.gather(*tasks, return_exceptions=True)

async def cleanup_symbol(symbol_key: str):
    """Bereinigt Ressourcen für ein Symbol"""
    # Collector stoppen
    if symbol_key in collectors:
        await collectors[symbol_key].stop()
        del collectors[symbol_key]
    
    # Broadcast-Task stoppen
    if symbol_key in broadcast_tasks:
        broadcast_tasks[symbol_key].cancel()
        try:
            await broadcast_tasks[symbol_key]
        except asyncio.CancelledError:
            pass
        del broadcast_tasks[symbol_key]
    
    # Queue entfernen
    if symbol_key in data_queues:
        del data_queues[symbol_key]
    
    # Clients entfernen
    if symbol_key in symbol_clients:
        del symbol_clients[symbol_key]
    
    logger.info(f"🧹 Cleaned up resources for {symbol_key}")

# WebSocket-Endpunkte
@router.websocket("/ws/{symbol}")
async def websocket_legacy(ws: WebSocket, symbol: str):
    await websocket_handler(ws, symbol, "spot")

@router.websocket("/ws/{symbol}/{market}/trades")
async def websocket_legacy_trades(ws: WebSocket, symbol: str, market: str):
    await websocket_handler(ws, symbol, market)

@router.websocket("/ws/{symbol}/{market}")
async def websocket_trades(ws: WebSocket, symbol: str, market: str):
    await websocket_handler(ws, symbol, market)

# REST-Endpunkte
@router.post("/publish")
async def publish_trade(trade: Dict[str, Any] = Body(...)):
    """Veröffentlicht einen Trade (für Tests und Integration)"""
    try:
        symbol = trade["symbol"]
        market = trade.get("market", "spot")
        symbol_key = f"{symbol}_{market}"
        
        # In Redis speichern
        await redis_manager.add_trade(symbol, trade, market)
        
        # Broadcast an Clients
        await broadcast_trade(symbol_key, trade)
        
        return {"status": "success"}
    except KeyError as e:
        raise HTTPException(400, f"Missing field: {e}")

@router.get("/trades")
async def get_trades(
    symbol: str = Query("BTCUSDT"),
    market: str = Query("spot"),
    limit: int = Query(100, gt=0, le=1000)
) -> List[Dict]:
    """Holt historische Trades mit hoher Geschwindigkeit"""
    return await redis_manager.get_recent_trades(symbol, market, limit)

@router.post("/backfill")
async def backfill(
    symbol: str = Body(...),
    market: str = Body("spot"),
    until: str = Body(...),
    granularity: str = Body("1min"),
    limit: int = Body(200)
):
    """Startet einen Backfill-Job"""
    try:
        until_dt = datetime.fromisoformat(until.rstrip('Z')).replace(tzinfo=timezone.utc)
        async with BitgetBackfill() as manager:
            count = await manager.history(symbol, market, until_dt, granularity, limit)
        return {"status": "success", "candles": count}
    except ValueError as e:
        raise HTTPException(400, f"Invalid date: {e}")