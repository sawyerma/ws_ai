import asyncio
import logging
import json
from datetime import datetime
from market.binance.services.binance_client import BinanceWebSocketClient
from market.binance.historical import HistoricalDataEngine
from market.binance.config import SystemConfig
from market.binance.storage.redis_manager import RedisManager
from market.binance.storage.clickhouse_manager import ClickHouseManager
from market.binance.services.auto_remediation import AutoRemediationSystem
from backend.core.services.aggregator import UnifiedCandleAggregator
from models.trade import UnifiedTrade, MarketType

logger = logging.getLogger("binance-collector")

class BinanceDataCollector:
    def __init__(self, config: SystemConfig):
        self.config = config
        self.redis = RedisManager(config)
        self.ch = ClickHouseManager(config, self.redis)
        self.aggregators = {res: UnifiedCandleAggregator(res) for res in config.resolutions}
        self.ws_clients = {}
        self.historical_engines = {}
        self.remediation = AutoRemediationSystem()
        self.tasks = []
        self.running = False
        
        # Komponenten registrieren
        self.remediation.register_component("binance_websocket")
        self.remediation.register_component("binance_rest_api")
        self.remediation.register_component("redis_storage")
        self.remediation.register_component("clickhouse_storage")

    async def start(self):
        self.running = True
        await self.redis.connect()
        await self.ch.connect()
        await self.remediation.start()
        
        # Laden des gespeicherten Zustands
        state = await self.redis.load_state(self.config.state_persist_key)
        # Hier können wir den Zustand verwenden, um z.B. Backfill fortzusetzen
        
        # Starte WebSockets
        for symbol in self.config.futures_symbols:
            await self._start_websocket(symbol, True)
        for symbol in self.config.spot_symbols:
            await self._start_websocket(symbol, False)
        
        # Starte Backfills
        for symbol in self.config.futures_symbols:
            await self._start_backfill(symbol, True)
        for symbol in self.config.spot_symbols:
            await self._start_backfill(symbol, False)
        
        # Starte Candle-Flush-Task
        self.tasks.append(asyncio.create_task(self._candle_flush_task()))
        
        logger.info("Binance data collector started")

    async def _start_websocket(self, symbol: str, is_futures: bool):
        try:
            ws_client = BinanceWebSocketClient(
                symbol,
                self.config,
                self._handle_trade,
                is_futures
            )
            key = f"{symbol}_{'futures' if is_futures else 'spot'}"
            self.ws_clients[key] = ws_client
            task = asyncio.create_task(ws_client.connect())
            self.tasks.append(task)
        except Exception as e:
            await self.remediation.handle_failure("binance_websocket", e)

    async def _start_backfill(self, symbol: str, is_futures: bool):
        try:
            engine = HistoricalDataEngine(
                symbol, 
                self.config, 
                is_futures,
                self.redis,
                self.ch,
                self.aggregators
            )
            key = f"{symbol}_{'futures' if is_futures else 'spot'}"
            self.historical_engines[key] = engine
            task = asyncio.create_task(engine.run_backfill())
            self.tasks.append(task)
        except Exception as e:
            await self.remediation.handle_failure("binance_rest_api", e)

    async def _handle_trade(self, trade: dict):
        try:
            # Konvertiere zu UnifiedTrade
            unified_trade = UnifiedTrade(
                exchange="binance",
                symbol=trade['symbol'],
                market=MarketType.usdtm if trade.get('is_futures', False) else MarketType.spot,
                price=trade['price'],
                size=trade['size'],
                side=trade['side'],
                timestamp=trade['timestamp'],
                exchange_id=trade['id']
            )
            
            await self.redis.save_trade(trade)
            await self.ch.save_trade(trade)
            
            # Verwende UnifiedCandleAggregator
            for aggregator in self.aggregators.values():
                candle = aggregator.process_trade(unified_trade)
                if candle:
                    await self.ch.save_candle(candle)
            
            logger.debug(f"Processed trade: {trade['symbol']} @ {trade['price']}")
        except Exception as e:
            logger.error(f"Error handling trade: {str(e)}")
            await self.remediation.handle_failure("redis_storage", e)
            await self.remediation.handle_failure("clickhouse_storage", e)

    async def _candle_flush_task(self):
        while self.running:
            await asyncio.sleep(10)
            try:
                for aggregator in self.aggregators.values():
                    candles = aggregator.flush_all()
                    for candle in candles:
                        await self.ch.save_candle(candle)
            except Exception as e:
                logger.error(f"Error flushing candles: {str(e)}")

    async def stop(self):
        self.running = False
        logger.info("Stopping Binance data collector...")
        
        # Stoppe alle laufenden Tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Warte auf das Ende der Tasks
        done, pending = await asyncio.wait(
            self.tasks,
            timeout=self.config.shutdown_timeout,
            return_when=asyncio.ALL_COMPLETED
        )
        
        for task in pending:
            logger.warning(f"Task did not complete in time: {task.get_name()}")
        
        # Stoppe alle Komponenten
        for client in self.ws_clients.values():
            await client.stop()
        for engine in self.historical_engines.values():
            await engine.stop()
        
        # Zustand speichern
        state = {
            # Hier den aktuellen Zustand des Collectors speichern
            "shutdown_time": datetime.utcnow().isoformat()
        }
        await self.redis.save_state(self.config.state_persist_key, state)
        
        await self.redis.close()
        await self.ch.close()
        await self.remediation.stop()
        
        logger.info("Binance data collector stopped")
