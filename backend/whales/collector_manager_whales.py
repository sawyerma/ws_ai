import asyncio
import logging
from whales.config_whales import Config
from whales.collectors.blockchain_collector_whales import EthereumCollector, BinanceCollector, PolygonCollector
from whales.collectors.token_collector_whales import EthereumTokenCollector, BinanceTokenCollector, PolygonTokenCollector

logger = logging.getLogger(__name__)

class CollectorManager:
    def __init__(self):
        self.collectors = {}
        self.collector_classes = {
            "ethereum": EthereumCollector,
            "binance": BinanceCollector,
            "polygon": PolygonCollector,
            "ethereum_tokens": EthereumTokenCollector,
            "binance_tokens": BinanceTokenCollector,
            "polygon_tokens": PolygonTokenCollector
        }
    
    async def init_from_config(self):
        # Aktiviere nur Chains mit konfigurierten API-Keys
        for chain in ["ethereum", "binance", "polygon"]:
            if getattr(Config, f"{chain.upper()}_API_KEY", ""):
                await self.start_collector(chain)
                await self.start_collector(f"{chain}_tokens")
    
    async def start_collector(self, collector_name: str):
        if collector_name in self.collectors:
            logger.warning(f"Collector {collector_name} already running")
            return
        
        if collector_name not in self.collector_classes:
            logger.error(f"No collector class for {collector_name}")
            return
        
        collector = self.collector_classes[collector_name]()
        await collector.start()
        self.collectors[collector_name] = collector
        logger.info(f"✅ {collector_name.replace('_', ' ').capitalize()} started")
    
    async def stop_collector(self, collector_name: str):
        if collector_name not in self.collectors:
            logger.warning(f"Collector {collector_name} not active")
            return
        
        await self.collectors[collector_name].stop()
        del self.collectors[collector_name]
        logger.info(f"🛑 {collector_name.replace('_', ' ').capitalize()} stopped")
    
    async def stop_all(self):
        for name in list(self.collectors.keys()):
            await self.stop_collector(name)

collector_manager = CollectorManager()
