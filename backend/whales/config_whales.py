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
    
    # API Keys - mit automatischem Fallback
    ETHEREUM_API_KEY = os.getenv("ETHEREUM_API_KEY", "")
    BSC_API_KEY = os.getenv("BSC_API_KEY", "")
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
    
    # Fallback API Keys (kostenlose Keys für Tests/Demo)
    FALLBACK_API_KEYS = {
        "ethereum": "YourApiKeyToken",  # Etherscan free tier
        "bsc": "YourApiKeyToken",       # BSCScan free tier
        "polygon": "YourApiKeyToken"    # PolygonScan free tier
    }
    
    # Preise
    PRICE_UPDATE_INTERVAL = int(os.getenv("PRICE_UPDATE_INTERVAL", 300))
    
    # Backfill-Konfiguration (minimal)
    BACKFILL_ENABLED = True
    BACKFILL_BATCH_SIZE = 1000  # Blöcke pro Batch
    
    # Intelligente API-Call-Zählung
    DAILY_API_LIMIT = 100000  # Etherscan/BSCScan/PolygonScan Daily Limit
    NIGHT_BACKFILL_HOUR = 23  # 23:00-24:00 Uhr intensive Backfill
    LIVE_WHALE_SAFETY_BUFFER = 10  # Puffer für Live-Whales um 23:00
    
    # Täglicher Reset um Mitternacht
    API_RESET_HOUR = 0  # 00:00 Uhr
    
    # Backfill-Ziel: 2017
    BACKFILL_TARGET_BLOCK_2017 = 4000000  # Ethereum Block ~Januar 2017
    
    # Historische Prioritäts-Blöcke (Bull-Runs)
    HISTORICAL_PRIORITY_BLOCKS = {
        "ethereum": [
            (4000000, 5000000),    # 2017 Bull-Run
            (13000000, 15000000),  # 2021 Bull-Run
        ],
        "binance": [
            (1000000, 2000000),    # 2021 Bull-Run
        ],
        "polygon": [
            (15000000, 20000000),  # 2021 Bull-Run
        ]
    }
    
    @classmethod
    def get_api_key(cls, chain: str) -> str:
        """
        Hole API-Key für eine Chain mit automatischem Fallback
        1. Versuche Frontend/User-API-Key
        2. Fallback auf kostenlose API-Keys
        3. Fallback auf leeren String (für Tests)
        """
        # Mapping für Chain-Namen zu Config-Attributen
        key_mapping = {
            "ethereum": cls.ETHEREUM_API_KEY,
            "bsc": cls.BSC_API_KEY,
            "polygon": cls.POLYGON_API_KEY
        }
        
        # Primärer API-Key (von Frontend/User)
        primary_key = key_mapping.get(chain, "")
        
        # Prüfe ob echter Key (nicht Platzhalter)
        if primary_key and not primary_key.startswith("YOUR_") and primary_key != "":
            return primary_key
        
        # Fallback auf kostenlose API-Keys
        fallback_key = cls.FALLBACK_API_KEYS.get(chain, "")
        if fallback_key and fallback_key != "YourApiKeyToken":
            return fallback_key
        
        # Letzter Fallback: leerer String für Tests
        return ""
    
    @classmethod
    def has_valid_api_key(cls, chain: str) -> bool:
        """Prüfe ob ein gültiger API-Key verfügbar ist"""
        key = cls.get_api_key(chain)
        return bool(key and key != "YourApiKeyToken" and not key.startswith("YOUR_"))
    
    @classmethod
    def is_using_fallback_api(cls, chain: str) -> bool:
        """Prüfe ob Fallback-API verwendet wird"""
        key_mapping = {
            "ethereum": cls.ETHEREUM_API_KEY,
            "bsc": cls.BSC_API_KEY,
            "polygon": cls.POLYGON_API_KEY
        }
        
        primary_key = key_mapping.get(chain, "")
        return not (primary_key and not primary_key.startswith("YOUR_") and primary_key != "")
    
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
