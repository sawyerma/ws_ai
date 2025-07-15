import os
from dotenv import load_dotenv

# .env laden
load_dotenv()

class Settings:
    """
    Projektweite Settings für die Trading-API.
    """
    APP_TITLE = "Trading API"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s %(levelname)s %(message)s")

    # CORS
    CORS_ALLOW_ORIGINS = ["*"]
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]

    # Pfad zum Frontend (relative Angabe von hier: core/)
    FRONTEND_DIR = os.getenv(
        "FRONTEND_DIR",
        os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    )

    # ClickHouse-Verbindungsparameter
    CH_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
    CH_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    CH_DATABASE = os.getenv("CLICKHOUSE_DB", "bitget")
    CH_USER = os.getenv("CLICKHOUSE_USER", "default")
    CH_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")

    # Trading System Settings
    TRADING_ENABLED = os.getenv("TRADING_ENABLED", "false").lower() == "true"
    MAX_CONCURRENT_STRATEGIES = int(os.getenv("MAX_CONCURRENT_STRATEGIES", "10"))
    MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "10.0"))
    MAX_DRAWDOWN = float(os.getenv("MAX_DRAWDOWN", "0.05"))
    RISK_CHECK_INTERVAL = int(os.getenv("RISK_CHECK_INTERVAL", "1000"))  # milliseconds

    # Grid Trading Settings
    MIN_GRID_LEVELS = int(os.getenv("MIN_GRID_LEVELS", "3"))
    MAX_GRID_LEVELS = int(os.getenv("MAX_GRID_LEVELS", "100"))
    DEFAULT_SPREAD_PERCENTAGE = float(os.getenv("DEFAULT_SPREAD_PERCENTAGE", "0.1"))

    # Bitget API Settings
    BITGET_API_KEY = os.getenv("BITGET_API_KEY", "")
    BITGET_SECRET_KEY = os.getenv("BITGET_SECRET_KEY", "")
    BITGET_PASSPHRASE = os.getenv("BITGET_PASSPHRASE", "")
    BITGET_SANDBOX = os.getenv("BITGET_SANDBOX", "true").lower() == "true"

    # Kafka Settings
    KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
    KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "trading-system")
    KAFKA_COMMANDS_TOPIC = os.getenv("KAFKA_COMMANDS_TOPIC", "trading_commands")
    KAFKA_MARKET_DATA_TOPIC = os.getenv("KAFKA_MARKET_DATA_TOPIC", "market_data")

    # Redis Settings
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # JWT Settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Instanziiere globale Settings
settings = Settings()
