import os
from dataclasses import dataclass

@dataclass
class BinanceConfig:
    api_key: str = os.getenv("BINANCE_API_KEY", "")
    api_secret: str = os.getenv("BINANCE_API_SECRET", "")
    max_requests_per_minute: int = 1200
    max_connections: int = 50
    historical_block_size: int = 300  # 5 Minuten in Sekunden

@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", 6379))
    db: int = int(os.getenv("REDIS_DB", 0))
    dlq_db: int = 1  # Separate DB für Dead Letter Queue

@dataclass
class ClickHouseConfig:
    host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    port: int = int(os.getenv("CLICKHOUSE_PORT", 9000))
    user: str = os.getenv("CLICKHOUSE_USER", "default")
    password: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    max_retries: int = 3
    retry_delay: float = 1.0
    queue_size: int = 10000

@dataclass
class SystemConfig:
    binance: BinanceConfig = BinanceConfig()
    redis: RedisConfig = RedisConfig()
    ch_config: ClickHouseConfig = ClickHouseConfig()
    max_historical_workers: int = 50
    backfill_interval: str = "1s"
    symbols: list = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"]
    futures_symbols: list = ["BTCUSDT", "ETHUSDT"]
    spot_symbols: list = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"]
    resolutions: list = [1, 60, 300, 900]  # 1s, 1m, 5m, 15m
    state_persist_key: str = "binance:collector_state"
    shutdown_timeout: int = 30  # Sekunden
