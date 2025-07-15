# /backend/core/ws/ws_whales.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import logging
import asyncio
import clickhouse_connect

# Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

CLICKHOUSE_HOST = "localhost"
CLICKHOUSE_PORT = 8123
CLICKHOUSE_USER = "default"
CLICKHOUSE_PASSWORD = ""
CLICKHOUSE_DB = "bitget"

router = APIRouter()

active_connections: List[WebSocket] = []

def get_client():
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )

async def send_json(websocket: WebSocket, data: Dict[str, Any]):
    await websocket.send_json(data)

async def broadcast_json(data: Dict[str, Any]):
    for ws in list(active_connections):
        try:
            await send_json(ws, data)
        except Exception:
            try:
                await ws.close()
            except Exception:
                pass
            if ws in active_connections:
                active_connections.remove(ws)

@router.websocket("/ws/whales")
async def ws_whales(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"[WS] Client connected: {websocket.client}")
    try:
        # Send the last 10 whale events immediately (upon connection)
        client = get_client()
        sql = "SELECT event_id, ts, chain, tx_hash, from_addr, to_addr, token, symbol, amount, is_native, exchange FROM whale_events ORDER BY ts DESC LIMIT 10"
        result = client.query(sql)
        latest_events = [dict(zip(result.column_names, row)) for row in result.result_rows]
        for event in reversed(latest_events):
            await send_json(websocket, event)
        # Listen for new events in polling loop (sub-second delay for near-real-time)
        last_seen_id = latest_events[0]['event_id'] if latest_events else None
        while True:
            await asyncio.sleep(1.5)
            sql = "SELECT event_id, ts, chain, tx_hash, from_addr, to_addr, token, symbol, amount, is_native, exchange FROM whale_events ORDER BY ts DESC LIMIT 1"
            result = client.query(sql)
            if result.result_rows:
                event = dict(zip(result.column_names, result.result_rows[0]))
                if event['event_id'] != last_seen_id:
                    await send_json(websocket, event)
                    last_seen_id = event['event_id']
    except WebSocketDisconnect:
        logger.info(f"[WS] Client disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"Error in /ws/whales: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
