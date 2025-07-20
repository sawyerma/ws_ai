import os
import ssl
from dataclasses import dataclass, field
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
    
    # API Credentials (can be updated dynamically)
    api_key: str = os.getenv("BITGET_API_KEY", "PUBLIC_ACCESS")
    secret_key: str = os.getenv("BITGET_SECRET_KEY", "")
    passphrase: str = os.getenv("BITGET_PASSPHRASE", "")
    
    # Static Rate Limits (base values)
    max_rps: int = 8
    historical_rps: float = 3.0
    
    # Dynamic Properties for Free/Premium Mode
    @property
    def is_premium(self) -> bool:
        """Check if premium features are enabled"""
        return self.api_key and self.api_key != "PUBLIC_ACCESS" and len(self.api_key) > 10
    
    @property
    def effective_max_rps(self) -> int:
        """Get current rate limit based on account type"""
        return 120 if self.is_premium else self.max_rps
    
    @property
    def effective_historical_rps(self) -> float:
        """Get historical data rate limit based on account type"""
        return 50.0 if self.is_premium else self.historical_rps
    
    @property
    def max_symbols_per_connection(self) -> int:
        """Maximum symbols per WebSocket connection"""
        return 100 if self.is_premium else 10
    
    @property
    def available_resolutions(self) -> List[int]:
        """Available time resolutions based on account type"""
        if self.is_premium:
            return [1, 5, 15, 60, 300, 900, 3600]  # Including 1s for premium
        return [60, 300, 900, 3600]  # Limited for free
    
    @property
    def max_historical_days(self) -> int:
        """Maximum days for historical data requests"""
        return 365 if self.is_premium else 30
    
    def update_credentials(self, api_key: str, secret_key: str, passphrase: str):
        """Update API credentials dynamically"""
        self.api_key = api_key if api_key else "PUBLIC_ACCESS"
        self.secret_key = secret_key
        self.passphrase = passphrase
    
    # Market Type Mappings
    market_mappings: Dict = field(default_factory=lambda: {
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
    })

@dataclass
class BinanceConfig:
    ws_url: str = "wss://stream.binance.com:9443/ws"
    api_key: str = os.getenv("BINANCE_API_KEY", "")
    secret_key: str = os.getenv("BINANCE_SECRET_KEY", "")
    max_rps: int = 10

@dataclass
class SystemConfig:
    # Auto-discovered symbols (will be populated)
    symbols: List[str] = field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "SOLUSDT"])  # Default fallback
    market_types: List[str] = field(default_factory=lambda: ["spot", "usdtm"])  # Default markets
    
    # Symbol selection criteria
    min_volume_24h: float = 1000000.0  # Minimum $1M volume
    base_max_symbols_per_market: int = 30   # Base max symbols per market type
    
    # Resolution settings (base values)
    base_resolutions: List[int] = field(default_factory=lambda: [60, 300, 900])  # Base resolutions
    deduplication_window: int = 3600
    
    # Historical target dates per symbol
    historical_target_dates: Dict[str, datetime] = field(default_factory=lambda: {
        "BTCUSDT": datetime(2020, 1, 1, tzinfo=timezone.utc),
        "ETHUSDT": datetime(2021, 1, 1, tzinfo=timezone.utc)
    })
    
    # Dynamic methods (use dependency injection to avoid circular imports)
    def get_effective_market_types(self, bitget_config) -> List[str]:
        """Get available market types based on account type"""
        base_markets = ["spot", "usdtm"]
        if bitget_config.is_premium:
            return base_markets + ["coinm", "usdcm"]  # Add premium markets
        return base_markets
    
    def get_max_symbols_per_market(self, bitget_config) -> int:
        """Get maximum symbols per market based on account type"""
        if bitget_config.is_premium:
            return 150  # Premium allows more symbols
        return self.base_max_symbols_per_market
    
    def get_resolutions(self, bitget_config) -> List[int]:
        """Get available resolutions based on account type"""
        return bitget_config.available_resolutions
    
    def get_total_max_symbols(self, bitget_config) -> int:
        """Total maximum symbols across all markets"""
        market_types = self.get_effective_market_types(bitget_config)
        max_symbols = self.get_max_symbols_per_market(bitget_config)
        return len(market_types) * max_symbols
    
    def update_for_premium(self, bitget_config):
        """Update configuration when premium features are activated"""
        if bitget_config.is_premium:
            # Expand market coverage
            if "coinm" not in self.market_types:
                self.market_types.extend(["coinm", "usdcm"])
            
            # Update historical targets for more pairs
            additional_targets = {
                "BNBUSDT": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "ADAUSDT": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "DOTUSDT": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "LINKUSDT": datetime(2021, 1, 1, tzinfo=timezone.utc),
            }
            self.historical_target_dates.update(additional_targets)
    
    def get_active_symbols_for_market(self, market_type: str, bitget_config) -> List[str]:
        """Get active symbols for a specific market type"""
        # This would be populated by symbol discovery
        # For now, return a subset based on limits
        all_symbols = self.symbols
        max_symbols = self.get_max_symbols_per_market(bitget_config)
        return all_symbols[:max_symbols]

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
