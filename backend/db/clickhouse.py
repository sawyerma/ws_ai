import clickhouse_connect
import os
import logging
import traceback
import threading
from typing import List, Dict, Any, Optional

# Structured logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = "default"
CLICKHOUSE_PASSWORD = ""
CLICKHOUSE_DB = "bitget"

# Connection Pool Implementation
_client_lock = threading.Lock()
_client_instance = None
_connection_count = 0

def get_client():
    """Get ClickHouse client with connection pooling for better performance"""
    global _client_instance, _connection_count
    
    if _client_instance is None:
        with _client_lock:
            if _client_instance is None:
                try:
                    _client_instance = clickhouse_connect.get_client(
                        host=CLICKHOUSE_HOST,
                        port=CLICKHOUSE_PORT,
                        username=CLICKHOUSE_USER,
                        password=CLICKHOUSE_PASSWORD,
                        database=CLICKHOUSE_DB,
                    )
                    logger.info(f"ClickHouse connection pool initialized: {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}")
                except Exception as e:
                    logger.error(f"Failed to create ClickHouse client: {e}")
                    traceback.print_exc()
                    raise
    
    _connection_count += 1
    if _connection_count % 100 == 0:
        logger.debug(f"ClickHouse connection pool used {_connection_count} times")
    
    return _client_instance

# --- Ping für Health-Checks ---
def ping() -> bool:
    """Health check for ClickHouse connection"""
    try:
        client = get_client()
        result = client.query('SELECT 1')
        return result.result_set[0][0] == 1
    except Exception as e:
        logger.error(f"ClickHouse ping failed: {e}")
        traceback.print_exc()
        return False

# --- Coin Settings: Insert/Update ---
def upsert_coin_setting(
    exchange: str,
    symbol: str,
    market: str,
    store_live: int,
    load_history: int,
    history_until: Optional[str],
    favorite: int,
    db_resolution: int,
    chart_resolution: str,
):
    """Insert or update coin settings with error handling"""
    try:
        client = get_client()
        table = f"{exchange}_coin_settings"  # Exchange-spezifische Tabelle
        sql = f"""
        INSERT INTO {table}
        (symbol, market, store_live, load_history, history_until, favorite, db_resolution, chart_resolution, updated_at)
        VALUES
        (%(symbol)s, %(market)s, %(store_live)s, %(load_history)s, %(history_until)s, %(favorite)s, %(db_resolution)s, %(chart_resolution)s, now())
        """
        client.command(
            sql,
            {
                "symbol": symbol,
                "market": market,
                "store_live": store_live,
                "load_history": load_history,
                "history_until": history_until,
                "favorite": favorite,
                "db_resolution": db_resolution,
                "chart_resolution": chart_resolution,
            }
        )
        logger.info(f"Upserted coin setting: {exchange}/{symbol}/{market}")
    except Exception as e:
        logger.error(f"Error upserting coin setting {exchange}/{symbol}/{market}: {e}")
        traceback.print_exc()
        raise

# --- Coin Settings: Lesen ---
def fetch_coin_settings(symbol: Optional[str] = None, market: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch coin settings with error handling"""
    try:
        client = get_client()
        sql = "SELECT symbol, market, store_live, load_history, history_until, favorite, db_resolution, chart_resolution, updated_at FROM coin_settings"
        conditions = []
        params = {}
        if symbol:
            conditions.append("symbol = %(symbol)s")
            params["symbol"] = symbol
        if market:
            conditions.append("market = %(market)s")
            params["market"] = market
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY symbol, market"
        
        result = client.query(sql, params)
        settings = [dict(zip(result.column_names, row)) for row in result.result_rows]
        logger.info(f"Fetched {len(settings)} coin settings")
        return settings
    except Exception as e:
        logger.error(f"Error fetching coin settings: {e}")
        traceback.print_exc()
        return []

# --- Alle Symbole für Dropdown ---
def fetch_symbols() -> List[Dict[str, Any]]:
    """Fetch available symbols with error handling"""
    try:
        client = get_client()
        sql = """
        SELECT DISTINCT symbol, market
        FROM coin_settings
        ORDER BY symbol, market
        """
        result = client.query(sql)
        symbols = [dict(zip(result.column_names, row)) for row in result.result_rows]
        logger.info(f"Fetched {len(symbols)} symbols")
        return symbols
    except Exception as e:
        logger.error(f"Error fetching symbols: {e}")
        traceback.print_exc()
        return []

# --- Trades: Insert ---
def insert_trade(
    symbol: str,
    market: str,
    price: float,
    size: float,
    side: str,
    ts: str,
):
    """Insert trade with error handling"""
    try:
        client = get_client()
        sql = """
        INSERT INTO trades (symbol, market, price, size, side, ts)
        VALUES (%(symbol)s, %(market)s, %(price)s, %(size)s, %(side)s, %(ts)s)
        """
        client.command(
            sql,
            {
                "symbol": symbol,
                "market": market,
                "price": price,
                "size": size,
                "side": side,
                "ts": ts,
            }
        )
        # Log every 100th trade to avoid spam
        if hasattr(insert_trade, 'counter'):
            insert_trade.counter += 1
        else:
            insert_trade.counter = 1
            
        if insert_trade.counter % 100 == 0:
            logger.info(f"Inserted {insert_trade.counter} trades (latest: {symbol}/{market} {price} {side})")
            
    except Exception as e:
        logger.error(f"Error inserting trade {symbol}/{market}: {e}")
        traceback.print_exc()
        raise

# --- Trades: Lesen ---
def fetch_trades(
    symbol: str,
    market: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """Fetch trades with error handling"""
    try:
        client = get_client()
        sql = """
        SELECT symbol, market, price, size, side, ts
        FROM trades
        WHERE symbol = %(symbol)s AND market = %(market)s
        """
        params = {"symbol": symbol, "market": market}
        if start:
            sql += " AND ts >= %(start)s"
            params["start"] = start
        if end:
            sql += " AND ts <= %(end)s"
            params["end"] = end
        sql += " ORDER BY ts DESC LIMIT %(limit)s"
        params["limit"] = limit
        
        result = client.query(sql, params)
        trades = [dict(zip(result.column_names, row)) for row in result.result_rows]
        logger.info(f"Fetched {len(trades)} trades for {symbol}/{market}")
        return trades
    except Exception as e:
        logger.error(f"Error fetching trades for {symbol}/{market}: {e}")
        traceback.print_exc()
        return []

# --- Bars: Insert ---
def insert_bar(
    symbol: str,
    market: str,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float,
    ts: str,
):
    """Insert bar/candle with error handling"""
    try:
        client = get_client()
        sql = """
        INSERT INTO bars (symbol, market, open, high, low, close, volume, ts)
        VALUES (%(symbol)s, %(market)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s, %(ts)s)
        """
        client.command(
            sql,
            {
                "symbol": symbol,
                "market": market,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "ts": ts,
            }
        )
        # Log every 50th bar to avoid spam
        if hasattr(insert_bar, 'counter'):
            insert_bar.counter += 1
        else:
            insert_bar.counter = 1
            
        if insert_bar.counter % 50 == 0:
            logger.info(f"Inserted {insert_bar.counter} bars (latest: {symbol}/{market} {close})")
            
    except Exception as e:
        logger.error(f"Error inserting bar {symbol}/{market}: {e}")
        traceback.print_exc()
        raise

# --- Bars: Lesen ---
def fetch_bars(
    exchange: str,
    symbol: str,
    market: str,
    resolution: int,
    limit: int = 1000,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetch bars/candles with error handling"""
    try:
        client = get_client()
        table = f"{exchange}_bars"  # Exchange-spezifische Tabelle
        sql = f"""
        SELECT symbol, market, resolution, open, high, low, close, volume, trades, ts
        FROM {table}
        WHERE symbol = %(symbol)s AND market = %(market)s AND resolution = %(resolution)s
        """
        params = {
            "symbol": symbol,
            "market": market,
            "resolution": resolution
        }
        
        if start:
            sql += " AND ts >= %(start)s"
            params["start"] = start
        if end:
            sql += " AND ts <= %(end)s"
            params["end"] = end
        
        sql += " ORDER BY ts DESC LIMIT %(limit)s"
        params["limit"] = limit
        
        result = client.query(sql, params)
        bars = [dict(zip(result.column_names, row)) for row in result.result_rows]
        logger.info(f"Fetched {len(bars)} bars for {exchange}/{symbol}/{market} (resolution: {resolution}s)")
        return bars
    except Exception as e:
        logger.error(f"Error fetching bars for {exchange}/{symbol}/{market}: {e}")
        traceback.print_exc()
        return []
