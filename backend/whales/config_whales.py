import os
from typing import Dict, Any
from dotenv import load_dotenv

# .env laden
load_dotenv()

class Config:
    """
    Whale Monitoring System Konfiguration
    """
    # ClickHouse-Verbindungsparameter (nutzt die gleichen wie Trading)
    CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
    CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
    
    # API Keys
    ETHEREUM_API_KEY = os.getenv("ETHEREUM_API_KEY", "")
    BSC_API_KEY = os.getenv("BSC_API_KEY", "")
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
    
    # Preise
    PRICE_UPDATE_INTERVAL = int(os.getenv("PRICE_UPDATE_INTERVAL", 300))
    
    # Coin-Konfiguration
    COIN_CONFIG: Dict[str, Dict[str, Any]] = {
        "BTC": {"threshold_usd": 100_000_000, "coingecko_id": "bitcoin", "priority": 1},
        "ETH": {"threshold_usd": 25_000_000, "coingecko_id": "ethereum", "priority": 1},
        "USDT": {"threshold_usd": 100_000_000, "coingecko_id": "tether", "priority": 1},
        "SOL": {"threshold_usd": 10_000_000, "coingecko_id": "solana", "priority": 2},
        "BNB": {"threshold_usd": 5_000_000, "coingecko_id": "binancecoin", "priority": 2},
        "XRP": {"threshold_usd": 10_000_000, "coingecko_id": "ripple", "priority": 2},
        "ADA": {"threshold_usd": 1_000_000, "coingecko_id": "cardano", "priority": 3},
        "AVAX": {"threshold_usd": 2_000_000, "coingecko_id": "avalanche-2", "priority": 3},
        "SUI": {"threshold_usd": 2_000_000, "coingecko_id": "sui", "priority": 3},
        "SEI": {"threshold_usd": 1_000_000, "coingecko_id": "sei-network", "priority": 3},
        "USDC": {"threshold_usd": 50_000_000, "coingecko_id": "usd-coin", "priority": 4},
        "BUSD": {"threshold_usd": 50_000_000, "coingecko_id": "binance-usd", "priority": 4},
    }
    
    # Chain-spezifische Konfiguration
    CHAIN_CONFIG = {
        "ethereum": {
            "api_url": "https://api.etherscan.io/api",
            "api_key_env": "ETHEREUM_API_KEY",
            "native_symbol": "ETH"
        },
        "binance": {
            "api_url": "https://api.bscscan.com/api",
            "api_key_env": "BSC_API_KEY",
            "native_symbol": "BNB"
        },
        "polygon": {
            "api_url": "https://api.polygonscan.com/api",
            "api_key_env": "POLYGON_API_KEY",
            "native_symbol": "MATIC"
        }
    }

# Instanziiere globale Whale-Config
config = Config()
