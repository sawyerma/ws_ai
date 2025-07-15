"""
Redis Cache Service für DarkMa Trading System
Optimiert für minimale Latenz und wartbaren Code
"""

import redis
import json
import os
import logging
from typing import Optional, Any, Union
from functools import wraps
from datetime import timedelta

logger = logging.getLogger(__name__)

# Redis-Konfiguration aus Umgebungsvariablen
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Log the configuration for debugging
logger.info(f"Redis configuration: {REDIS_HOST}:{REDIS_PORT} (DB: {REDIS_DB})")

# Standard TTL-Werte (in Sekunden)
DEFAULT_TTL = 60  # 1 Minute
SYMBOLS_TTL = 300  # 5 Minuten für Symbole
TICKER_TTL = 10  # 10 Sekunden für Ticker-Daten
OHLC_TTL = 30  # 30 Sekunden für OHLC-Daten


class RedisCache:
    """Minimalistischer Redis-Cache-Client"""
    
    def __init__(self):
        self._client = None
        self._connection_failed = False
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Lazy-Loading Redis-Client mit Connection-Pooling"""
        if self._connection_failed:
            return None
            
        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    db=REDIS_DB,
                    decode_responses=True,
                    socket_connect_timeout=1,
                    socket_timeout=1,
                    retry_on_timeout=False
                )
                # Test-Ping
                self._client.ping()
                logger.info(f"Redis connected: {REDIS_HOST}:{REDIS_PORT}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Cache disabled.")
                self._connection_failed = True
                return None
                
        return self._client
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return None
            
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.debug(f"Cache get error for {key}: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
        """Set value in cache with TTL"""
        if not self.client:
            return False
            
        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.debug(f"Cache set error for {key}: {e}")
        return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.client:
            return False
            
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache delete error for {key}: {e}")
        return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.client:
            return 0
            
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
        except Exception as e:
            logger.debug(f"Cache clear pattern error for {pattern}: {e}")
        return 0


# Globale Cache-Instanz
cache = RedisCache()


def cached(key_prefix: str, ttl: int = DEFAULT_TTL):
    """
    Decorator für Cache-fähige Funktionen
    
    Beispiel:
        @cached("symbols", ttl=SYMBOLS_TTL)
        async def get_symbols():
            return expensive_db_query()
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Cache-Key generieren
            cache_key = f"{key_prefix}"
            if args:
                cache_key += f":{':'.join(str(a) for a in args)}"
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
            
            # Aus Cache holen
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Funktion ausführen und cachen
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Cache-Key generieren
            cache_key = f"{key_prefix}"
            if args:
                cache_key += f":{':'.join(str(a) for a in args)}"
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
            
            # Aus Cache holen
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Funktion ausführen und cachen
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        # Return async or sync wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Cache-Keys für verschiedene Daten-Typen
class CacheKeys:
    """Zentrale Verwaltung von Cache-Keys"""
    SYMBOLS = "symbols"
    TICKER = "ticker:{symbol}:{market}"
    OHLC = "ohlc:{symbol}:{market}:{resolution}:{limit}"
    ORDERBOOK = "orderbook:{symbol}:{market}:{depth}"
    TRADES = "trades:{symbol}:{market}:{limit}"
    COINS_ACTIVE = "coins:active"
    WHALE_ALERTS = "whale:alerts:{symbol}"
