import redis.asyncio as aioredis
import logging
import hashlib
import json
import gzip
import time
from market.bitget.config import redis_config, system_config
from market.bitget.utils.circuit_breaker import CircuitBreaker

logger = logging.getLogger("redis-manager")

class RedisConnectionPool:
    def __init__(self):
        self._pool = None
        self._circuit_breaker = CircuitBreaker()
        
    async def initialize(self):
        try:
            self._pool = aioredis.ConnectionPool(
                host=redis_config.host,
                port=redis_config.port,
                password=redis_config.password,
                max_connections=redis_config.pool_size,
                **TLS_CONFIG
            )
            logger.info("Redis connection pool initialized")
        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            raise
            
    async def get_connection(self):
        if not self._pool:
            await self.initialize()
        return aioredis.Redis(connection_pool=self._pool)
        
    async def execute(self, command: str, *args, **kwargs):
        async def _execute():
            async with await self.get_connection() as conn:
                return await getattr(conn, command)(*args, **kwargs)
        return await self._circuit_breaker.execute(_execute)

class RedisManager:
    def __init__(self):
        self._pool = RedisConnectionPool()
        self._dedupe_cache = {}
        
    async def initialize(self):
        await self._pool.initialize()
        
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
