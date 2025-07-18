import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, Any
from db.clickhouse_whales import insert_whale_event, is_duplicate
from whales.services.price_service_whales import price_service
from whales.config_whales import Config

logger = logging.getLogger(__name__)

class BlockchainCollector:
    # Erweiterte Exchange-Mappings mit Geolocation
    EXCHANGE_LOCATIONS = {
        # Ethereum
        "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE": {
            "exchange": "Binance", "country": "Malta", "city": "Valletta", "chain": "ethereum"
        },
        "0x28C6c06298d514Db089934071355E5743bf21d60": {
            "exchange": "Binance", "country": "Malta", "city": "Valletta", "chain": "ethereum"
        },
        "0x06959153B974D0D5fDfd87D561db6d8d4FA0bb0B": {
            "exchange": "Bitget", "country": "Singapore", "city": "Singapore", "chain": "ethereum"
        },
        "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43": {
            "exchange": "Coinbase", "country": "USA", "city": "San Francisco", "chain": "ethereum"
        },
        
        # Binance Smart Chain
        "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3": {
            "exchange": "Binance", "country": "Malta", "city": "Valletta", "chain": "binance"
        },
        "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8": {
            "exchange": "Binance", "country": "Malta", "city": "Valletta", "chain": "binance"
        },
        
        # Polygon
        "0x06959153B974D0D5fDfd87D561db6d8d4FA0bb0B": {
            "exchange": "Bitget", "country": "Singapore", "city": "Singapore", "chain": "polygon"
        },
        "0x71660c4005BA85c37cCeD5156124Dd39DEa8a4F1": {
            "exchange": "Coinbase", "country": "USA", "city": "San Francisco", "chain": "polygon"
        }
    }
    
    def __init__(self, chain: str):
        self.chain = chain
        self.chain_config = Config.CHAIN_CONFIG[chain]
        self.api_key = getattr(Config, self.chain_config["api_key_env"])
        self.base_url = self.chain_config["api_url"]
        self.last_block = 0
        self.running = False
        self.session = None
        self.native_symbol = self.chain_config["native_symbol"]
    
    async def start(self):
        self.running = True
        self.session = aiohttp.ClientSession()
        self.last_block = await self.get_latest_block() - 10
        asyncio.create_task(self.run())
        logger.info(f"{self.chain.capitalize()} Collector gestartet")
    
    async def stop(self):
        self.running = False
        if self.session:
            await self.session.close()
        logger.info(f"{self.chain.capitalize()} Collector gestoppt")
    
    async def run(self):
        while self.running:
            try:
                current_block = await self.get_latest_block()
                
                if current_block > self.last_block:
                    for block_num in range(self.last_block + 1, current_block + 1):
                        await self.process_block(block_num)
                    self.last_block = current_block
                
                await asyncio.sleep(10 if self.chain == "ethereum" else 15)
            except Exception as e:
                logger.error(f"Run loop error: {e}")
                await asyncio.sleep(30)

    async def get_latest_block(self) -> int:
        try:
            params = {"module": "proxy", "action": "eth_blockNumber", "apikey": self.api_key}
            async with self.session.get(self.base_url, params=params, timeout=10) as response:
                data = await response.json()
                return int(data.get("result", "0x0"), 16)
        except Exception as e:
            logger.error(f"Blocknummernfehler: {e}")
            return self.last_block

    async def process_block(self, block_number: int):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                params = {
                    "module": "proxy",
                    "action": "eth_getBlockByNumber",
                    "tag": hex(block_number),
                    "boolean": "true",
                    "apikey": self.api_key
                }
                
                async with self.session.get(self.base_url, params=params, timeout=15) as response:
                    data = await response.json()
                    transactions = data.get("result", {}).get("transactions", [])
                    
                    # Verarbeite Transaktionen parallel
                    await asyncio.gather(*[
                        self.process_transaction(tx)
                        for tx in transactions
                        if self.is_whale_transaction(tx)
                    ])
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f"Block {block_number} Fehler (Versuch {attempt+1}): {e}. Warte {wait}s")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Überspringe Block {block_number} nach {max_retries} Versuchen")
                    break

    def is_whale_transaction(self, tx: dict) -> bool:
        # Filtere nur Transaktionen mit Wert
        return tx.get("input") == "0x" and tx.get("value") != "0x0"
    
    async def process_transaction(self, tx: dict):
        try:
            if await is_duplicate(tx["hash"], self.chain):
                return
            
            value_wei = int(tx["value"], 16)
            value_native = value_wei / 10**18
            
            # Ermittle Coin-Konfiguration
            coin_config = Config.COIN_CONFIG.get(self.native_symbol, {})
            threshold = coin_config.get("threshold_usd", 1_000_000)
            
            # Hole Preis
            coin_price = price_service.get_price(coin_config.get("coingecko_id", self.native_symbol.lower())) or 0
            usd_value = value_native * coin_price
            
            # Prüfe Whale-Schwelle
            if usd_value < threshold:
                return
            
            # Ermittle Standorte
            from_location = self.get_location(tx["from"])
            to_location = self.get_location(tx["to"])
            
            # Cross-Border-Erkennung
            is_cross_border = from_location["country"] != to_location["country"]
            
            # Erstelle Event
            event = {
                "ts": datetime.now(),
                "chain": self.chain,
                "tx_hash": tx["hash"],
                "from_addr": tx["from"],
                "to_addr": tx["to"],
                "symbol": self.native_symbol,
                "amount": value_native,
                "is_native": 1,
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
                logger.info(f"🐋 {self.native_symbol} Whale: {value_native:,.2f} (${usd_value:,.0f})")
                
                # Spezial-Log für Cross-Border-Whales
                if is_cross_border and usd_value > 1_000_000:
                    logger.warning(f"🌍 Cross-border: {from_location['country']} → {to_location['country']} (${usd_value:,.0f})")
        except Exception as e:
            logger.error(f"Transaktionsverarbeitungsfehler: {e}")

    def get_location(self, address: str) -> dict:
        # Finde passende Location für die aktuelle Chain
        location = self.EXCHANGE_LOCATIONS.get(address, {
            "exchange": "",
            "country": "Unknown",
            "city": "Unknown"
        })
        
        # Prüfe ob Location zur aktuellen Chain passt
        if "chain" in location and location["chain"] != self.chain:
            return {
                "exchange": "",
                "country": "Unknown",
                "city": "Unknown"
            }
        
        return location

class EthereumCollector(BlockchainCollector):
    def __init__(self):
        super().__init__("ethereum")

class BinanceCollector(BlockchainCollector):
    def __init__(self):
        super().__init__("binance")

class PolygonCollector(BlockchainCollector):
    def __init__(self):
        super().__init__("polygon")
