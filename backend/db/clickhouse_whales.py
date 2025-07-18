import clickhouse_connect
import os
import logging
import traceback
import threading
from typing import Dict, Any, Optional
from datetime import datetime

# Structured logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = "default"
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
CLICKHOUSE_DB = "bitget"  # Nutzt die gleiche Datenbank wie Trading

# Connection Pool Implementation
_whale_client_lock = threading.Lock()
_whale_client_instance = None
_whale_connection_count = 0

def get_whale_client():
    """Get ClickHouse client with connection pooling for Whale system"""
    global _whale_client_instance, _whale_connection_count
    
    if _whale_client_instance is None:
        with _whale_client_lock:
            if _whale_client_instance is None:
                try:
                    _whale_client_instance = clickhouse_connect.get_client(
                        host=CLICKHOUSE_HOST,
                        port=CLICKHOUSE_PORT,
                        username=CLICKHOUSE_USER,
                        password=CLICKHOUSE_PASSWORD,
                        database=CLICKHOUSE_DB,
                    )
                    logger.info(f"Whale ClickHouse connection pool initialized: {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}")
                except Exception as e:
                    logger.error(f"Failed to create Whale ClickHouse client: {e}")
                    traceback.print_exc()
                    raise
    
    _whale_connection_count += 1
    if _whale_connection_count % 100 == 0:
        logger.debug(f"Whale ClickHouse connection pool used {_whale_connection_count} times")
    
    return _whale_client_instance

# --- Whale Events: Insert ---
async def insert_whale_event(event: Dict[str, Any]) -> bool:
    """Insert whale event with error handling"""
    try:
        client = get_whale_client()
        sql = """
        INSERT INTO whale_events
        (ts, chain, tx_hash, from_addr, to_addr, token, symbol, amount, is_native, exchange, 
         amount_usd, from_exchange, from_country, from_city, to_exchange, to_country, to_city, 
         is_cross_border, threshold_usd, coin_rank, source, created_at)
        VALUES
        (%(ts)s, %(chain)s, %(tx_hash)s, %(from_addr)s, %(to_addr)s, %(token)s, %(symbol)s, 
         %(amount)s, %(is_native)s, %(exchange)s, %(amount_usd)s, %(from_exchange)s, 
         %(from_country)s, %(from_city)s, %(to_exchange)s, %(to_country)s, %(to_city)s, 
         %(is_cross_border)s, %(threshold_usd)s, %(coin_rank)s, %(source)s, %(created_at)s)
        """
        
        # Bereite Parameter vor
        params = {
            "ts": event.get("ts", datetime.now()),
            "chain": event.get("chain", ""),
            "tx_hash": event.get("tx_hash", ""),
            "from_addr": event.get("from_addr", ""),
            "to_addr": event.get("to_addr", ""),
            "token": event.get("token", ""),
            "symbol": event.get("symbol", ""),
            "amount": event.get("amount", 0.0),
            "is_native": event.get("is_native", 0),
            "exchange": event.get("exchange", ""),
            "amount_usd": event.get("amount_usd", 0.0),
            "from_exchange": event.get("from_exchange", ""),
            "from_country": event.get("from_country", "Unknown"),
            "from_city": event.get("from_city", "Unknown"),
            "to_exchange": event.get("to_exchange", ""),
            "to_country": event.get("to_country", "Unknown"),
            "to_city": event.get("to_city", "Unknown"),
            "is_cross_border": event.get("is_cross_border", 0),
            "threshold_usd": event.get("threshold_usd", 0.0),
            "coin_rank": event.get("coin_rank", 3),
            "source": event.get("source", "direct_collector"),
            "created_at": datetime.now()
        }
        
        client.command(sql, params)
        
        # Log every 10th whale event to avoid spam
        if hasattr(insert_whale_event, 'counter'):
            insert_whale_event.counter += 1
        else:
            insert_whale_event.counter = 1
            
        if insert_whale_event.counter % 10 == 0:
            logger.info(f"Inserted {insert_whale_event.counter} whale events (latest: {event.get('symbol', 'N/A')} ${event.get('amount_usd', 0):,.0f})")
        
        return True
        
    except Exception as e:
        logger.error(f"Error inserting whale event {event.get('tx_hash', 'unknown')}: {e}")
        traceback.print_exc()
        return False

# --- Whale Events: Duplicate Check ---
async def is_duplicate(tx_hash: str, chain: str) -> bool:
    """Check if whale event already exists"""
    try:
        client = get_whale_client()
        sql = """
        SELECT COUNT(*) as count
        FROM whale_events
        WHERE tx_hash = %(tx_hash)s AND chain = %(chain)s
        """
        
        result = client.query(sql, {"tx_hash": tx_hash, "chain": chain})
        count = result.result_rows[0][0] if result.result_rows else 0
        
        return count > 0
        
    except Exception as e:
        logger.error(f"Error checking duplicate for {tx_hash}/{chain}: {e}")
        traceback.print_exc()
        return False

# --- Whale Events: Fetch ---
def fetch_whale_events(
    symbol: Optional[str] = None,
    chain: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 1000,
) -> list[Dict[str, Any]]:
    """Fetch whale events with error handling"""
    try:
        client = get_whale_client()
        sql = """
        SELECT ts, chain, tx_hash, from_addr, to_addr, token, symbol, amount, is_native, 
               exchange, amount_usd, from_exchange, from_country, from_city, to_exchange, 
               to_country, to_city, is_cross_border, threshold_usd, coin_rank, source, created_at
        FROM whale_events
        WHERE 1=1
        """
        params = {}
        
        if symbol:
            sql += " AND symbol = %(symbol)s"
            params["symbol"] = symbol
        if chain:
            sql += " AND chain = %(chain)s"
            params["chain"] = chain
        if start:
            sql += " AND ts >= %(start)s"
            params["start"] = start
        if end:
            sql += " AND ts <= %(end)s"
            params["end"] = end
            
        sql += " ORDER BY ts DESC LIMIT %(limit)s"
        params["limit"] = limit
        
        result = client.query(sql, params)
        events = [dict(zip(result.column_names, row)) for row in result.result_rows]
        logger.info(f"Fetched {len(events)} whale events")
        return events
        
    except Exception as e:
        logger.error(f"Error fetching whale events: {e}")
        traceback.print_exc()
        return []

# --- Coin Config: Upsert ---
def upsert_coin_config(
    symbol: str,
    chain: str,
    contract_addr: str,
    coingecko_id: str,
    decimals: int,
    threshold_usd: float,
    priority: int,
    active: int = 1
):
    """Insert or update coin config with error handling"""
    try:
        client = get_whale_client()
        sql = """
        INSERT INTO coin_config
        (symbol, chain, contract_addr, coingecko_id, decimals, threshold_usd, priority, active, last_updated)
        VALUES
        (%(symbol)s, %(chain)s, %(contract_addr)s, %(coingecko_id)s, %(decimals)s, %(threshold_usd)s, %(priority)s, %(active)s, now())
        """
        client.command(
            sql,
            {
                "symbol": symbol,
                "chain": chain,
                "contract_addr": contract_addr,
                "coingecko_id": coingecko_id,
                "decimals": decimals,
                "threshold_usd": threshold_usd,
                "priority": priority,
                "active": active,
            }
        )
        logger.info(f"Upserted coin config: {symbol}/{chain}")
    except Exception as e:
        logger.error(f"Error upserting coin config {symbol}/{chain}: {e}")
        traceback.print_exc()
        raise

# --- Coin Config: Fetch ---
def fetch_coin_configs(symbol: Optional[str] = None, chain: Optional[str] = None) -> list[Dict[str, Any]]:
    """Fetch coin configs with error handling"""
    try:
        client = get_whale_client()
        sql = """
        SELECT symbol, chain, contract_addr, coingecko_id, decimals, threshold_usd, priority, active, last_updated
        FROM coin_config
        WHERE active = 1
        """
        params = {}
        
        if symbol:
            sql += " AND symbol = %(symbol)s"
            params["symbol"] = symbol
        if chain:
            sql += " AND chain = %(chain)s"
            params["chain"] = chain
            
        sql += " ORDER BY priority, symbol"
        
        result = client.query(sql, params)
        configs = [dict(zip(result.column_names, row)) for row in result.result_rows]
        logger.info(f"Fetched {len(configs)} coin configs")
        return configs
        
    except Exception as e:
        logger.error(f"Error fetching coin configs: {e}")
        traceback.print_exc()
        return []
