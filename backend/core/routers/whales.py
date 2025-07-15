# /backend/routers/whales.py

from fastapi import APIRouter, Query
from typing import List, Optional, Dict, Any
import logging
from whale.settings import fetch_coins
import clickhouse_connect

router = APIRouter(prefix="/api", tags=["whales"])

# Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

CLICKHOUSE_HOST = "localhost"
CLICKHOUSE_PORT = 8123
CLICKHOUSE_USER = "default"
CLICKHOUSE_PASSWORD = ""
CLICKHOUSE_DB = "bitget"

def get_client():
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )

@router.get("/coins", response_model=List[Dict[str, Any]])
def get_coins(
    symbol: Optional[str] = Query(None),
    chain: Optional[str] = Query(None),
    exchange: Optional[str] = Query(None),
    active: Optional[int] = Query(None)
):
    """
    Liefert alle Coins/Token aus dem Mapping (Mapping/Settings für Whale-Detection).
    """
    coins = fetch_coins(symbol=symbol, chain=chain, exchange=exchange, active=active)
    logger.info(f"[API] /coins -> {len(coins)} coins returned")
    return coins

@router.get("/whale_events", response_model=List[Dict[str, Any]])
def get_whale_events(
    symbol: Optional[str] = Query(None),
    exchange: Optional[str] = Query(None),
    since: Optional[str] = Query(None),  # z.B. "2024-07-01 00:00:00"
    until: Optional[str] = Query(None),  # z.B. "2024-07-02 00:00:00"
    limit: int = Query(200)
):
    """
    Liefert Whale-Events (on-chain Großtransfers), filterbar nach Symbol, Exchange und Zeitraum.
    """
    try:
        client = get_client()
        sql = "SELECT event_id, ts, chain, tx_hash, from_addr, to_addr, token, symbol, amount, is_native, exchange FROM whale_events"
        conditions = []
        params = {}
        if symbol:
            conditions.append("symbol = %(symbol)s")
            params["symbol"] = symbol
        if exchange:
            conditions.append("exchange = %(exchange)s")
            params["exchange"] = exchange
        if since:
            conditions.append("ts >= %(since)s")
            params["since"] = since
        if until:
            conditions.append("ts <= %(until)s")
            params["until"] = until
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY ts DESC LIMIT %(limit)s"
        params["limit"] = limit
        result = client.query(sql, params)
        events = [dict(zip(result.column_names, row)) for row in result.result_rows]
        logger.info(f"[API] /whale_events -> {len(events)} events returned (filters: {params})")
        return events
    except Exception as e:
        logger.error(f"Error fetching whale_events: {e}")
        return []
