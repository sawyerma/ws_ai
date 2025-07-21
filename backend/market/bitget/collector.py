import asyncio
import logging
from market.bitget.services.bitget_client import BitgetWebSocketClient
from market.bitget.storage.redis_manager import redis_manager
from market.bitget.config import system_config, bitget_config

logger = logging.getLogger("collector")

class BitgetCollector:
    """Hochleistungs-Collector für Bitget Marktdaten"""
    
    def __init__(self, symbol: str, market_type: str, data_queue: asyncio.Queue):
        self.symbol = symbol
        self.market_type = market_type
        self.data_queue = data_queue
        self.client = BitgetWebSocketClient([symbol], market_type)
        self.running = False
        self.process_task = None
        
    async def start(self):
        """Startet den Collector mit maximaler Performance"""
        if self.running:
            return
            
        self.running = True
        
        # Starte Datenverarbeitung parallel
        self.process_task = asyncio.create_task(self._process_data())
        
        # WebSocket Client starten
        await self.client.start()
        
        logger.info(f"🚀 Collector started for {self.symbol} ({self.market_type})")
        
    async def _process_data(self):
        """Verarbeitet eingehende Daten mit minimaler Latenz"""
        while self.running:
            # Hier würden normalerweise Daten aus dem WebSocket kommen
            # Für dieses Beispiel simulieren wir Daten
            await asyncio.sleep(0.1)
            trade = {
                "symbol": self.symbol,
                "market": self.market_type,
                "price": 50000.0 + (0.1 * (id(self) % 100)),
                "size": 0.01,
                "side": "buy" if (id(self) % 2) == 0 else "sell",
                "ts": int(time.time() * 1000),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Zur Weiterverarbeitung in die Queue geben
            await self.data_queue.put(trade)
            
            # In Redis speichern
            await redis_manager.add_trade(
                trade["symbol"],
                trade,
                self.market_type
            )
    
    async def stop(self):
        """Stoppt den Collector mit sofortiger Wirkung"""
        if not self.running:
            return
            
        self.running = False
        
        # Client stoppen
        await self.client.stop()
        
        # Verarbeitungstask beenden
        if self.process_task:
            self.process_task.cancel()
            try:
                await self.process_task
            except asyncio.CancelledError:
                pass
                
        logger.info(f"🛑 Collector stopped for {self.symbol} ({self.market_type})")
    
    def get_status(self) -> dict:
        """Gibt aktuellen Status zurück (für Monitoring)"""
        return {
            "symbol": self.symbol,
            "market_type": self.market_type,
            "running": self.running,
            "queue_size": self.data_queue.qsize(),
            "stats": self.client.get_connection_stats() if self.client else {}
        }