import asyncio
import logging
import time
from datetime import datetime, timezone
from market.bitget.services.bitget_rest import BitgetRestAPI
from market.bitget.storage.redis_manager import redis_manager
from market.bitget.config import bitget_config
from market.bitget.utils.adaptive_rate_limiter import get_rate_limiter

logger = logging.getLogger("historical")

class BitgetBackfill:
    """Hochleistungs-Backfill für historische Daten"""
    
    def __init__(self):
        self.rest_api = BitgetRestAPI()
        self.rate_limiter = get_rate_limiter("historical-backfill")
        self.rate_limiter.update_base_rps(bitget_config.effective_historical_rps)
        self.batch_size = 500  # Optimiert für Bulk-Inserts
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc, tb):
        await self.rest_api.close()
        
    async def history(
        self, 
        symbol: str, 
        market_type: str,
        end_date: datetime, 
        granularity: str = "1min", 
        limit: int = 1000
    ):
        """Holt historische Daten mit maximaler Geschwindigkeit"""
        logger.info(f"📅 Backfilling {symbol} until {end_date} ({granularity})")
        
        # Granularity mapping
        resolution_map = {
            "1min": "1m",
            "5min": "5m",
            "15min": "15m",
            "1h": "1H",
            "4h": "4H",
            "1d": "1D"
        }
        
        if granularity not in resolution_map:
            raise ValueError(f"Unsupported granularity: {granularity}")
        
        # API-Parameter
        params = {
            "symbol": symbol,
            "granularity": resolution_map[granularity],
            "limit": min(limit, 2000),
            "endTime": int(end_date.timestamp() * 1000)
        }
        
        # Batch-Verarbeitung für hohen Durchsatz
        all_candles = []
        total_candles = 0
        batch_count = 0
        
        while total_candles < limit:
            # Rate Limiting beachten
            await self.rate_limiter.acquire()
            
            # Daten abrufen
            if market_type == "spot":
                response = await self.rest_api.fetch_spot_candles(**params)
            else:
                params["productType"] = "USDT-FUTURES"
                response = await self.rest_api.fetch_futures_candles(**params)
                
            if not response or response.get("code") != "00000":
                logger.error(f"❌ Backfill failed for {symbol}: {response.get('msg')}")
                break
                
            candles = response.get("data", [])
            if not candles:
                break
                
            # Zur Batch-Verarbeitung hinzufügen
            all_candles.extend(candles)
            total_candles += len(candles)
            
            # Nächsten Batch vorbereiten
            last_candle_ts = int(candles[-1][0])
            params["endTime"] = last_candle_ts - 1  # Nächstes Segment
            
            # Batch voll? Dann speichern
            if len(all_candles) >= self.batch_size:
                await self._store_batch(symbol, market_type, all_candles)
                batch_count += 1
                all_candles = []
                
            if total_candles >= limit:
                break
                
        # Restliche Daten speichern
        if all_candles:
            await self._store_batch(symbol, market_type, all_candles)
            batch_count += 1
            
        logger.info(f"✅ Backfill completed: {total_candles} candles in {batch_count} batches")
        return total_candles
        
    async def _store_batch(self, symbol: str, market_type: str, candles: list):
        """Speichert einen Batch von Candles mit maximaler Geschwindigkeit"""
        try:
            # Paralleles Speichern in Redis
            tasks = [
                redis_manager.add_candle(symbol, candle, market_type)
                for candle in candles
            ]
            
            # Asynchron parallel verarbeiten
            await asyncio.gather(*tasks)
            
            logger.debug(f"💾 Stored batch of {len(candles)} candles for {symbol}")
            
        except Exception as e:
            logger.error(f"❌ Batch storage failed: {str(e)}")