import asyncio
import aiohttp
import logging
from datetime import datetime
from whales.config_whales import Config

logger = logging.getLogger(__name__)

class PriceService:
    def __init__(self):
        self.prices = {}
        self.update_interval = Config.PRICE_UPDATE_INTERVAL
        self.coin_ids = {v["coingecko_id"]: v["coingecko_id"] for v in Config.COIN_CONFIG.values()}
        self.last_update = datetime.min

    async def start(self):
        await self.update_prices()
        asyncio.create_task(self.update_loop())

    async def update_loop(self):
        while True:
            await asyncio.sleep(self.update_interval)
            await self.update_prices()

    async def update_prices(self):
        if (datetime.now() - self.last_update).total_seconds() < self.update_interval:
            return
            
        try:
            # Erstelle Liste aller zu aktualisierenden Coins
            coin_ids = ",".join(self.coin_ids.keys())
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for coin_id in self.coin_ids:
                            if coin_id in data and "usd" in data[coin_id]:
                                self.prices[coin_id] = data[coin_id]["usd"]
                        logger.info(f"Updated prices for {len(self.prices)} coins")
                    else:
                        logger.error(f"Price API error: {response.status}")
            
            self.last_update = datetime.now()
        except Exception as e:
            logger.error(f"Price update error: {str(e)}")

    def get_price(self, coin_id: str) -> float:
        return self.prices.get(coin_id.lower(), 0.0)

price_service = PriceService()
