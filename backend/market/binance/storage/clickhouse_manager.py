import asyncio
import logging
import json
from clickhouse_driver import Client
from clickhouse_driver.errors import Error as ClickhouseError
from market.binance.config import SystemConfig
from market.binance.storage.redis_manager import RedisManager

logger = logging.getLogger("clickhouse-storage")

class ClickHouseManager:
    def __init__(self, config: SystemConfig, redis: RedisManager):
        self.config = config
        self.redis = redis
        self.client = None
        self.queue = asyncio.Queue(maxsize=config.ch_config.queue_size)
        self.processing_task = None
        self.running = True

    async def connect(self):
        self.client = Client(
            host=self.config.ch_config.host,
            port=self.config.ch_config.port,
            user=self.config.ch_config.user,
            password=self.config.ch_config.password
        )
        self._create_tables()
        self.processing_task = asyncio.create_task(self.process_queue())

    def _create_tables(self):
        try:
            # Tabellen werden per Migration erstellt
            logger.info("Verifying ClickHouse tables...")
        except ClickhouseError as e:
            logger.error(f"Table verification error: {str(e)}")
            raise

    async def _retry_execute(self, query, params=None):
        for attempt in range(self.config.ch_config.max_retries):
            try:
                if params:
                    self.client.execute(query, params)
                else:
                    self.client.execute(query)
                return True
            except ClickhouseError as e:
                if attempt < self.config.ch_config.max_retries - 1:
                    delay = self.config.ch_config.retry_delay * (2 ** attempt)
                    logger.warning(f"ClickHouse error, retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"ClickHouse error after {self.config.ch_config.max_retries} attempts: {str(e)}")
                    return False
        return False

    async def _send_to_dlq(self, data_type, data):
        try:
            await self.redis.dlq_redis.rpush(
                f"dlq:{data_type}", 
                json.dumps(data, default=str)
            )
            logger.info(f"Sent to DLQ: {data_type}")
        except Exception as e:
            logger.critical(f"Failed to send to DLQ: {str(e)}")

    async def _process_trade(self, trade):
        query = """
        INSERT INTO binance_trades 
        (trade_id, symbol, market, price, size, side, ts)
        VALUES """
        params = [(
            trade['id'],
            trade['symbol'],
            trade['market'],
            trade['price'],
            trade['quantity'],
            1 if trade['is_buyer_maker'] else 2,
            trade['timestamp']
        )]
        if not await self._retry_execute(query, params):
            await self._send_to_dlq("trade", trade)

    async def _process_candle(self, candle):
        query = """
        INSERT INTO binance_bars 
        (symbol, market, resolution, open, high, low, close, volume, trades, ts)
        VALUES """
        params = [(
            candle['symbol'],
            candle['market'],
            candle['resolution'],
            candle['open'],
            candle['high'],
            candle['low'],
            candle['close'],
            candle['volume'],
            candle['trades'],
            candle['ts']
        )]
        if not await self._retry_execute(query, params):
            await self._send_to_dlq("candle", candle)

    async def save_trade(self, trade: dict):
        await self.queue.put(('trade', trade))

    async def save_trades(self, trades: list):
        for trade in trades:
            await self.save_trade(trade)

    async def save_candle(self, candle: dict):
        await self.queue.put(('candle', candle))

    async def process_queue(self):
        while self.running or not self.queue.empty():
            try:
                item_type, data = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                if item_type == 'trade':
                    await self._process_trade(data)
                elif item_type == 'candle':
                    await self._process_candle(data)
                self.queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing queue item: {str(e)}")

    async def close(self):
        self.running = False
        if self.processing_task:
            await asyncio.wait_for(self.processing_task, timeout=10)
        if self.client:
            self.client.disconnect()
        logger.info("ClickHouse connection closed")
