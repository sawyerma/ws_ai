import aioredis
import logging
import json
from datetime import datetime
from market.binance.config import SystemConfig

logger = logging.getLogger("redis-storage")

class RedisManager:
    def __init__(self, config: SystemConfig):
        self.config = config
        self.redis = None
        self.dlq_redis = None

    async def connect(self):
        self.redis = await aioredis.from_url(
            f"redis://{self.config.redis.host}:{self.config.redis.port}/{self.config.redis.db}",
            encoding="utf-8",
            decode_responses=False
        )
        self.dlq_redis = await aioredis.from_url(
            f"redis://{self.config.redis.host}:{self.config.redis.port}/{self.config.redis.dlq_db}",
            encoding="utf-8",
            decode_responses=False
        )
        logger.info("Connected to Redis")

    async def save_trade(self, trade: dict):
        if not self.redis:
            await self.connect()
        
        try:
            key = f"binance:{trade['market']}:trades:{trade['symbol']}"
            value = json.dumps(trade, default=self._json_serial)
            await self.redis.zadd(key, {value: trade['timestamp'].timestamp()})
            await self.redis.expire(key, 86400 * 7)  # 7 Tage Retention
        except Exception as e:
            logger.error(f"Error saving trade: {str(e)}")

    async def save_trades(self, trades: list):
        if not self.redis:
            await self.connect()
        
        pipeline = self.redis.pipeline()
        for trade in trades:
            key = f"binance:{trade['market']}:trades:{trade['symbol']}"
            value = json.dumps(trade, default=self._json_serial)
            pipeline.zadd(key, {value: trade['timestamp'].timestamp()})
            pipeline.expire(key, 86400 * 7)
        await pipeline.execute()

    async def get_recent_trades(self, symbol: str, market: str, limit: int = 100):
        if not self.redis:
            await self.connect()
        
        key = f"binance:{market}:trades:{symbol}"
        trades = await self.redis.zrevrange(key, 0, limit - 1, withscores=False)
        return [json.loads(trade) for trade in trades]

    async def save_state(self, key: str, state: dict):
        if not self.redis:
            await self.connect()
        await self.redis.set(key, json.dumps(state))

    async def load_state(self, key: str) -> dict:
        if not self.redis:
            await self.connect()
        state = await self.redis.get(key)
        return json.loads(state) if state else {}

    def _json_serial(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    async def close(self):
        if self.redis:
            await self.redis.close()
        if self.dlq_redis:
            await self.dlq_redis.close()
        logger.info("Redis connection closed")
