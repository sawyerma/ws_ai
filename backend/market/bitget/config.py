import os
import ssl
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime, timezone

@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", 6380))
    password: str = os.getenv("REDIS_PASSWORD", "")
    pool_size: int = 20
    stream_maxlen: int = 50000
    orderbook_ttl: int = 30

@dataclass
class ClickHouseConfig:
    host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    port: int = int(os.getenv("CLICKHOUSE_PORT", 8123))
    database: str = "trading"
    username: str = os.getenv("CLICKHOUSE_USER", "default")
    password: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    batch_size: int = 1000
    unified_table: str = "candles_unified"

@dataclass
class BitgetConfig:
    # REST API
    rest_base_url: str = "https://api.bitget.com"
    
    # API Credentials
    api_key: str = os.getenv("BITGET_API_KEY", "")
    secret_key: str = os.getenv("BITGET_SECRET_KEY", "")
    passphrase: str = os.getenv("BITGET_PASSPHRASE", "")
    
    # Rate Limits
    max_rps: int = 8
    historical_rps: float = 3.0
    
    # Market Type Mappings
    market_mappings: Dict = {
        "spot": {
            "ws_url": "wss://ws.bitget.com/spot/v1/stream",
            "inst_type": "SP",
            "suffix": "_SPBL"
        },
        "usdtm": {
            "ws_url": "wss://ws.bitget.com/mix/v1/stream", 
            "inst_type": "UMCBL",
            "suffix": "_UMCBL"
        },
        "coinm": {
            "ws_url": "wss://ws.bitget.com/mix/v1/stream",
            "inst_type": "DMCBL", 
            "suffix": "_DMCBL"
        },
        "usdcm": {
            "ws_url": "wss://ws.bitget.com/mix/v1/stream",
            "inst_type": "CMCBL",
            "suffix": "_CMCBL"
        }
    }

@dataclass
class BinanceConfig:
    ws_url: str = "wss://stream.binance.com:9443/ws"
    api_key: str = os.getenv("BINANCE_API_KEY", "")
    secret_key: str = os.getenv("BINANCE_SECRET_KEY", "")
    max_rps: int = 10

@dataclass
class SystemConfig:
    # Auto-discovered symbols (will be populated)
    symbols: List[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]  # Default fallback
    market_types: List[str] = ["spot", "usdtm"]  # Default markets
    
    # Symbol selection criteria
    min_volume_24h: float = 1000000.0  # Minimum $1M volume
    max_symbols_per_market: int = 30   # Max symbols per market type
    
    # Resolution settings
    resolutions: List[int] = [1, 60, 300, 900]  # 1s, 1m, 5m, 15m
    deduplication_window: int = 3600
    
    # Historical target dates per symbol
    historical_target_dates: Dict[str, datetime] = {
        "BTCUSDT": datetime(2020, 1, 1, tzinfo=timezone.utc),
        "ETHUSDT": datetime(2021, 1, 1, tzinfo=timezone.utc)
    }

# TLS-Konfiguration
TLS_CONFIG = {
    "ssl": True,
    "ssl_ca_certs": os.getenv("SSL_CA_CERTS", None),
    "ssl_certfile": os.getenv("SSL_CERT_FILE", None),
    "ssl_keyfile": os.getenv("SSL_KEY_FILE", None),
    "ssl_cert_reqs": ssl.CERT_REQUIRED if os.getenv("SSL_VERIFY", "true") == "true" else ssl.CERT_NONE
}

# Konfigurationsinstanzen
redis_config = RedisConfig()
clickhouse_config = ClickHouseConfig()
bitget_config = BitgetConfig()
binance_config = BinanceConfig()
system_config = SystemConfig()
