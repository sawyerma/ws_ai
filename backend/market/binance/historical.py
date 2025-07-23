import asyncio
import logging
from datetime import datetime, timedelta
from market.binance.services.binance_rest import BinanceRestClient
from market.binance.config import SystemConfig

logger = logging.getLogger("binance-historical")

class HistoricalDataEngine:
    def __init__(self, symbol: str, config: SystemConfig, is_futures: bool, redis, ch, aggregators):
        self.symbol = symbol
        self.config = config
        self.is_futures = is_futures
        self.redis = redis
        self.ch = ch
        self.aggregators = aggregators
        self.rest_client = BinanceRestClient(config, is_futures)
        self.target_date = datetime(2020, 1, 1)
        self.current_date = datetime.utcnow()
        self.running = True
        self.state_key = f"backfill:{symbol}:{is_futures}"

    async def run_backfill(self):
        # Zustand laden
        state = await self.redis.load_state(self.state_key)
        if state:
            self.current_date = datetime.fromisoformat(state['current_date'])
            logger.info(f"Resuming backfill from {self.current_date}")
        
        market_type = "futures" if self.is_futures else "spot"
        logger.info(f"Starting {market_type} backfill for {self.symbol}")
        
        try:
            while self.current_date > self.target_date and self.running:
                end_time = self.current_date
                start_time = max(self.current_date - timedelta(minutes=5), self.target_date)
                
                trades = await self.rest_client.fetch_historical_trades(
                    self.symbol,
                    start_time,
                    end_time
                )
                
                if trades:
                    await self.redis.save_trades(trades)
                    await self.ch.save_trades(trades)
                    
                    for res, aggregator in self.aggregators.items():
                        for trade in trades:
                            candle = aggregator.process_trade(trade)
                            if candle:
                                await self.ch.save_candle(candle)
                        
                        candles = aggregator.flush_all()
                        for candle in candles:
                            await self.ch.save_candle(candle)
                    
                    logger.info(f"Processed {len(trades)} trades for {self.symbol}")
                
                self.current_date = start_time
                progress = self._calculate_progress()
                
                # Zustand speichern
                await self._save_progress()
                
                await asyncio.sleep(0.1)
            
            logger.info(f"Backfill completed for {self.symbol} ({market_type})")
        except Exception as e:
            logger.error(f"Backfill failed: {str(e)}")
        finally:
            await self.rest_client.close()
            await self._save_progress()

    def _calculate_progress(self) -> float:
        total_seconds = (datetime.utcnow() - self.target_date).total_seconds()
        completed_seconds = (datetime.utcnow() - self.current_date).total_seconds()
        return min(100.0, (completed_seconds / total_seconds) * 100)

    async def _save_progress(self):
        progress = {
            'current_date': self.current_date.isoformat(),
            'target_date': self.target_date.isoformat(),
            'progress': self._calculate_progress()
        }
        await self.redis.save_state(self.state_key, progress)

    async def stop(self):
        self.running = False
        await self._save_progress()
        logger.info(f"Historical engine stopped for {self.symbol}")
