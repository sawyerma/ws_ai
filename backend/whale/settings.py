# /backend/whale/settings.py

import clickhouse_connect
import os
import logging
import traceback
from typing import List, Dict, Any, Optional

# Structured logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = "default"
CLICKHOUSE_PASSWORD = ""
CLICKHOUSE_DB = "bitget"

def get_client():
    """Get ClickHouse client with error handling"""
    try:
        return clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            username=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
            database=CLICKHOUSE_DB,
        )
    except Exception as e:
        logger.error(f"Failed to create ClickHouse client: {e}")
        traceback.print_exc()
        raise

# --- Coins: Insert or Update ---
def upsert_coin(
    symbol: str,
    chain: str,
    contract_addr: str,
    is_native: int,
    exchange: str,
    active: int
):
    """
    Insert or update a coin mapping.
    """
    try:
        client = get_client()
        sql = """
        INSERT INTO coins
        (symbol, chain, contract_addr, is_native, exchange, active)
        VALUES
        (%(symbol)s, %(chain)s, %(contract_addr)s, %(is_native)s, %(exchange)s, %(active)s)
        """
        client.command(
            sql,
            {
                "symbol": symbol,
                "chain": chain,
                "contract_addr": contract_addr,
                "is_native": is_native,
                "exchange": exchange,
                "active": active,
            }
        )
        logger.info(f"Upserted coin: {symbol}/{chain} (exchange={exchange}, active={active})")
    except Exception as e:
        logger.error(f"Error upserting coin {symbol}/{chain}: {e}")
        traceback.print_exc()
        raise

# --- Coins: Read/Fetch ---
def fetch_coins(
    symbol: Optional[str] = None,
    chain: Optional[str] = None,
    exchange: Optional[str] = None,
    active: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetch coin mappings with optional filters.
    """
    try:
        client = get_client()
        sql = "SELECT symbol, chain, contract_addr, is_native, exchange, active FROM coins"
        conditions = []
        params = {}
        if symbol:
            conditions.append("symbol = %(symbol)s")
            params["symbol"] = symbol
        if chain:
            conditions.append("chain = %(chain)s")
            params["chain"] = chain
        if exchange:
            conditions.append("exchange = %(exchange)s")
            params["exchange"] = exchange
        if active is not None:
            conditions.append("active = %(active)s")
            params["active"] = active
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY symbol, chain"
        result = client.query(sql, params)
        coins = [dict(zip(result.column_names, row)) for row in result.result_rows]
        logger.info(f"Fetched {len(coins)} coins (filters: {params})")
        return coins
    except Exception as e:
        logger.error(f"Error fetching coins: {e}")
        traceback.print_exc()
        return []

# --- Coins: Delete ---
def delete_coin(symbol: str, chain: str):
    """
    Delete a coin mapping.
    """
    try:
        client = get_client()
        sql = "ALTER TABLE coins DELETE WHERE symbol = %(symbol)s AND chain = %(chain)s"
        client.command(sql, {"symbol": symbol, "chain": chain})
        logger.info(f"Deleted coin: {symbol}/{chain}")
    except Exception as e:
        logger.error(f"Error deleting coin {symbol}/{chain}: {e}")
        traceback.print_exc()
        raise

# --- Coins: Bulk Fetch for Mapping (Detection Helper) ---
def fetch_active_coin_map() -> Dict[str, Dict[str, Any]]:
    """
    Fetch all active coins, keyed by (symbol, chain), for fast lookup in Detection.
    Returns: {(symbol, chain): {rowdict}}
    """
    coins = fetch_coins(active=1)
    mapping = {(c['symbol'], c['chain']): c for c in coins}
    logger.info(f"Prepared active coin mapping: {len(mapping)} entries")
    return mapping
