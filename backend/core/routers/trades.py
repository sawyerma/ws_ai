import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Set, Any, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Body, HTTPException, Query
from core.routers.exchange_factory import ExchangeFactory
from models.trade import UnifiedTrade

router = APIRouter()
logger = logging.getLogger("trades-api")

# Globale WebSocket-Verwaltung für alle Exchanges
exchange_clients: Dict[str, Dict[str, Set[WebSocket]]] = {}

async def websocket_handler(ws: WebSocket, exchange: str, symbol: str, market: str):
    await ws.accept()
    symbol_key = f"{symbol}_{market}"
    
    # Client registrieren
    if exchange not in exchange_clients:
        exchange_clients[exchange] = {}
    if symbol_key not in exchange_clients[exchange]:
        exchange_clients[exchange][symbol_key] = set()
    exchange_clients[exchange][symbol_key].add(ws)

    # Redis Manager holen
    redis = ExchangeFactory.get_storage(exchange, "redis")
    if not redis:
        await ws.close(code=1003, reason="Exchange not supported")
        return

    # Letzte Trades senden
    try:
        trades = await redis.get_recent_trades(symbol, market, 30)
        for trade in reversed(trades):
            await ws.send_text(json.dumps({"type": "trade", "data": trade}))
    except Exception as e:
        logger.error(f"Trade snapshot failed: {str(e)}")

    # Live-Trades verarbeiten
    try:
        collector = ExchangeFactory.get_collector(exchange, symbol, market)
        if collector:
            while True:
                trade = await collector.trade_queue.get()
                await ws.send_text(json.dumps({"type": "trade", "data": trade}))
        else:
            logger.warning(f"No active collector for {exchange}/{symbol}/{market}")
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        exchange_clients[exchange][symbol_key].remove(ws)
        logger.info(f"WebSocket disconnected: {exchange}/{symbol}/{market}")

        # Cleanup wenn keine Clients mehr
        if not exchange_clients[exchange][symbol_key]:
            del exchange_clients[exchange][symbol_key]

# Unified WebSocket-Endpoints
@router.websocket("/ws/{exchange}/{symbol}/{market}")
async def websocket_unified(ws: WebSocket, exchange: str, symbol: str, market: str):
    await websocket_handler(ws, exchange, symbol, market)

# Legacy compatibility endpoints
@router.websocket("/ws/{symbol}")
async def websocket_legacy(ws: WebSocket, symbol: str):
    await websocket_handler(ws, "bitget", symbol, "spot")

@router.websocket("/ws/{symbol}/{market}/trades")
async def websocket_legacy_trades(ws: WebSocket, symbol: str, market: str):
    await websocket_handler(ws, "bitget", symbol, market)

@router.websocket("/ws/{symbol}/{market}")
async def websocket_trades(ws: WebSocket, symbol: str, market: str):
    await websocket_handler(ws, "bitget", symbol, market)

# Unified Publish-Endpoint
@router.post("/publish")
async def publish(trade: UnifiedTrade = Body(...)):
    try:
        redis = ExchangeFactory.get_storage(trade.exchange, "redis")
        if not redis:
            raise HTTPException(400, "Exchange not supported")
        
        await redis.add_trade(trade)
        
        # Broadcast an Subscriber
        symbol_key = f"{trade.symbol}_{trade.market.value}"
        for ws in set(exchange_clients.get(trade.exchange, {}).get(symbol_key, [])):
            try:
                await ws.send_text(json.dumps({"type": "trade", "data": trade.dict()}))
            except (WebSocketDisconnect, RuntimeError):
                exchange_clients[trade.exchange][symbol_key].discard(ws)
                
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Publish error: {str(e)}")
        raise HTTPException(500, f"Publish failed: {str(e)}")

# Unified GET-Endpoint
@router.get("/trades")
async def get_trades(
    exchange: str = Query("bitget"),
    symbol: str = Query("BTCUSDT"),
    market: str = Query("spot"),
    limit: int = Query(100, gt=0, le=1000)
) -> List[Dict]:
    redis = ExchangeFactory.get_storage(exchange, "redis")
    if not redis:
        raise HTTPException(400, "Exchange not supported")
    return await redis.get_recent_trades(symbol, market, limit)

# Unified Backfill-Endpoint
@router.post("/backfill")
async def backfill_endpoint(
    exchange: str = Body("bitget"),
    symbol: str = Body(...),
    until: str = Body(...),
    granularity: str = Body("1min"),
    limit: int = Body(200)
):
    try:
        until_dt = datetime.fromisoformat(until.rstrip('Z')).replace(tzinfo=timezone.utc)
        manager = ExchangeFactory.get_historical_manager(exchange)
        if not manager:
            raise HTTPException(400, "Exchange not supported")
        
        await manager.history(symbol, until_dt, granularity, limit)
        return {"status": "backfill completed"}
    
    except ValueError as e:
        raise HTTPException(400, f"Invalid datetime format: {str(e)}")
