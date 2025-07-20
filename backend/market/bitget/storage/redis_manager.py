import redis.asyncio as aioredis
import logging
import hashlib
import json
import gzip
import time
from typing import Dict, Any, Optional
from market.bitget.config import redis_config, system_config, TLS_CONFIG

logger = logging.getLogger("redis-manager")

class RedisConnectionPool:
    def __init__(self):
        self._pool = None
        self._connection_failures = 0
        self._last_failure_time = 0
        
    async def initialize(self):
        try:
            # Redis-spezifische SSL-Konfiguration (ohne TLS_CONFIG für WebSocket)
            redis_ssl_config = {}
            if redis_config.host not in ['localhost', '127.0.0.1']:
                # SSL nur für Remote-Verbindungen aktivieren
                redis_ssl_config = {
                    'ssl': True,
                    'ssl_check_hostname': False,
                    'ssl_cert_reqs': 'none'
                }
            
            self._pool = aioredis.ConnectionPool(
                host=redis_config.host,
                port=redis_config.port,
                password=redis_config.password if redis_config.password else None,
                max_connections=redis_config.pool_size,
                **redis_ssl_config
            )
            logger.info(f"✅ Redis connection pool initialized - Host: {redis_config.host}:{redis_config.port}")
        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {e}")
            raise
            
    async def get_connection(self):
        if not self._pool:
            await self.initialize()
        return aioredis.Redis(connection_pool=self._pool)
        
    async def execute(self, command: str, *args, **kwargs):
        """Führt Redis-Kommandos mit Fehlerbehandlung aus"""
        try:
            async with await self.get_connection() as conn:
                return await getattr(conn, command)(*args, **kwargs)
        except Exception as e:
            self._connection_failures += 1
            self._last_failure_time = time.time()
            logger.error(f"Redis command '{command}' failed: {e}")
            raise

class RedisManager:
    def __init__(self):
        self._pool = RedisConnectionPool()
        self._dedupe_cache = {}
        
    async def initialize(self):
        """Initialisiert Redis-Verbindung"""
        await self._pool.initialize()
        logger.info("✅ Redis Manager initialized")
    
    async def ping(self) -> bool:
        """Testet Redis-Verbindung"""
        try:
            # Direkte Redis-Verbindung für Ping
            redis_client = await self._pool.get_connection()
            result = await redis_client.ping()
            await redis_client.close()
            
            logger.info(f"✅ Redis ping successful: {result}")
            return result is True or result == b'PONG' or result == 'PONG'
        except Exception as e:
            logger.error(f"❌ Redis ping failed: {e}")
            return False
        
    async def add_trade(self, symbol: str, trade: dict, market_type: str = "spot") -> bool:
        trade["market_type"] = market_type
        trade_hash = self._generate_trade_hash(trade)
        
        if await self._is_duplicate(trade_hash):
            return False
            
        stream_key = f"trades:{symbol}:{market_type}"
        await self._pool.execute(
            "xadd",
            stream_key,
            {"data": self._compress_data(trade)},
            id=f"{trade['timestamp']}-0",
            maxlen=redis_config.stream_maxlen,
            approximate=True
        )
        
        self._dedupe_cache[trade_hash] = time.time()
        return True
    
    async def add_orderbook(self, symbol: str, orderbook_data: dict, market_type: str = "spot") -> bool:
        """Speichert Orderbuch-Daten (Premium Feature)"""
        try:
            orderbook_key = f"orderbook:{symbol}:{market_type}"
            
            # Orderbuch mit TTL speichern
            compressed_data = self._compress_data({
                "symbol": symbol,
                "market_type": market_type,
                "data": orderbook_data,
                "timestamp": int(time.time() * 1000)
            })
            
            await self._pool.execute(
                "setex", 
                orderbook_key, 
                redis_config.orderbook_ttl,  # 30 Sekunden TTL
                compressed_data
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store orderbook for {symbol}: {e}")
            return False
        
    def _generate_trade_hash(self, trade: dict) -> str:
        data = f"{trade['symbol']}:{trade['market_type']}:{trade['timestamp']}:{trade['price']}:{trade['size']}"
        return hashlib.sha256(data.encode()).hexdigest()
        
    async def _is_duplicate(self, trade_hash: str) -> bool:
        if trade_hash in self._dedupe_cache:
            return True
            
        exists = await self._pool.execute("exists", f"trade_dedup:{trade_hash}")
        if exists:
            return True
            
        await self._pool.execute(
            "setex", 
            f"trade_dedup:{trade_hash}", 
            system_config.deduplication_window, 
            "1"
        )
        return False
        
    def _compress_data(self, data: dict) -> bytes:
        return gzip.compress(json.dumps(data).encode())
        
    def _decompress_data(self, data: bytes) -> dict:
        return json.loads(gzip.decompress(data).decode())

redis_manager = RedisManager()
