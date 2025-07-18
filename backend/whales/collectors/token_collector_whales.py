import asyncio
import aiohttp
import logging
from datetime import datetime
from db.clickhouse_whales import insert_whale_event, is_duplicate
from whales.services.price_service_whales import price_service
from whales.config_whales import Config

logger = logging.getLogger(__name__)

class TokenCollector:
    # Chain-Konfiguration
    CHAIN_CONFIG = {
        "ethereum": {
            "api_url": "https://api.etherscan.io/api",
            "api_key": Config.ETHEREUM_API_KEY,
            "native_symbol": "ETH"
        },
        "binance": {
            "api_url": "https://api.bscscan.com/api",
            "api_key": Config.BSC_API_KEY,
            "native_symbol": "BNB"
        },
        "polygon": {
            "api_url": "https://api.polygonscan.com/api",
            "api_key": Config.POLYGON_API_KEY,
            "native_symbol": "MATIC"
        }
    }
    
    def __init__(self, chain: str):
        self.chain = chain
        self.config = self.CHAIN_CONFIG[chain]
        self.last_block = 0
        self.running = False
        self.session = None
        self.token_cache = {}
    
    async def start(self):
        self.running = True
        self.session = aiohttp.ClientSession()
        self.last_block = await self.get_latest_block() - 10
        asyncio.create_task(self.run())
        logger.info(f"{self.chain.capitalize()} Token Collector gestartet")
    
    async def stop(self):
        self.running = False
        if self.session:
            await self.session.close()
        logger.info(f"{self.chain.capitalize()} Token Collector gestoppt")
    
    async def run(self):
        while self.running:
            try:
                current_block = await self.get_latest_block()
                
                if current_block > self.last_block:
                    for block_num in range(self.last_block + 1, current_block + 1):
                        await self.process_token_block(block_num)
                    self.last_block = current_block
                
                await asyncio.sleep(15)
            except Exception as e:
                logger.error(f"Run loop error: {e}")
                await asyncio.sleep(30)

    async def get_latest_block(self) -> int:
        try:
            params = {"module": "proxy", "action": "eth_blockNumber", "apikey": self.config["api_key"]}
            async with self.session.get(self.config["api_url"], params=params, timeout=10) as response:
                data = await response.json()
                return int(data.get("result", "0x0"), 16)
        except Exception as e:
            logger.error(f"Blocknummernfehler: {e}")
            return self.last_block

    async def process_token_block(self, block_number: int):
        try:
            params = {
                "module": "account",
                "action": "tokentx",
                "startblock": block_number,
                "endblock": block_number,
                "sort": "asc",
                "apikey": self.config["api_key"]
            }
            
            async with self.session.get(self.config["api_url"], params=params, timeout=20) as response:
                data = await response.json()
                transfers = data.get("result", [])
                
                # Verarbeite Transfers parallel
                await asyncio.gather(*[
                    self.process_token_transfer(transfer)
                    for transfer in transfers
                ])
        except Exception as e:
            logger.error(f"Token block processing error: {e}")

    async def process_token_transfer(self, transfer: dict):
        try:
            # Prüfe auf Duplikat
            if await is_duplicate(transfer["hash"], self.chain):
                return
            
            # Ermittle Token-Details
            token_address = transfer["contractAddress"]
            token_symbol = transfer.get("tokenSymbol", "").upper()
            
            # Hole Token-Konfiguration
            coin_config = Config.COIN_CONFIG.get(token_symbol, {})
            threshold = coin_config.get("threshold_usd", 1_000_000)
            
            # Überspringe wenn nicht in der Prioritätenliste
            if not coin_config:
                return
            
            # Konvertiere Wert
            decimals = int(transfer.get("tokenDecimal", 18))
            value = float(transfer["value"]) / (10 ** decimals)
            
            # Ermittle Preis
            token_price = price_service.get_price(coin_config.get("coingecko_id", token_symbol.lower())) or 0
            usd_value = value * token_price
            
            # Prüfe Whale-Schwelle
            if usd_value < threshold:
                return
            
            # Ermittle Standorte (aus blockchain_collector importieren)
            from whales.collectors.blockchain_collector_whales import BlockchainCollector
            collector = BlockchainCollector(chain=self.chain)
            from_location = collector.get_location(transfer["from"])
            to_location = collector.get_location(transfer["to"])
            
            # Cross-Border-Erkennung
            is_cross_border = from_location["country"] != to_location["country"]
            
            # Erstelle Event
            event = {
                "ts": datetime.fromtimestamp(int(transfer.get("timeStamp", 0))),
                "chain": self.chain,
                "tx_hash": transfer["hash"],
                "from_addr": transfer["from"],
                "to_addr": transfer["to"],
                "token": token_address,
                "symbol": token_symbol,
                "amount": value,
                "is_native": 0,
                "exchange": from_location.get("exchange", "") or to_location.get("exchange", ""),
                "amount_usd": usd_value,
                "from_exchange": from_location.get("exchange", ""),
                "from_country": from_location.get("country", "Unknown"),
                "from_city": from_location.get("city", "Unknown"),
                "to_exchange": to_location.get("exchange", ""),
                "to_country": to_location.get("country", "Unknown"),
                "to_city": to_location.get("city", "Unknown"),
                "is_cross_border": int(is_cross_border),
                "threshold_usd": threshold,
                "coin_rank": coin_config.get("priority", 3)
            }
            
            if await insert_whale_event(event):
                logger.info(f"🪙 {token_symbol} Whale: {value:,.0f} (${usd_value:,.0f})")
                
                # Spezial-Log für Cross-Border-Whales
                if is_cross_border and usd_value > 1_000_000:
                    logger.warning(f"🌍 Cross-border token: {from_location['country']} → {to_location['country']} (${usd_value:,.0f})")
        except Exception as e:
            logger.error(f"Token transfer error: {e}")

class EthereumTokenCollector(TokenCollector):
    def __init__(self):
        super().__init__("ethereum")

class BinanceTokenCollector(TokenCollector):
    def __init__(self):
        super().__init__("binance")

class PolygonTokenCollector(TokenCollector):
    def __init__(self):
        super().__init__("polygon")
