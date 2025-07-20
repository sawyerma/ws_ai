import asyncio
import signal
import logging
from fastapi import FastAPI
import uvicorn
from market.bitget.config import (
    redis_config,  
    clickhouse_config,
    bitget_config,
    system_config
)
from market.bitget.services.symbol_manager import symbol_manager
from market.bitget.services.bitget_client import BitgetWebSocketClient
from market.bitget.api.ws_manager import ws_manager, handle_websocket_connection
from market.bitget.storage.redis_manager import redis_manager
from market.bitget.api.symbols_api import router as symbols_router

logger = logging.getLogger("trading-system")

app = FastAPI()
app.include_router(symbols_router, prefix="/api")

class TradingSystem:
    def __init__(self):
        self.ws_clients = []
        self.running = False
        
    async def start(self):
        self.running = True
        
        try:
            # Initialize Redis
            await redis_manager.initialize()
            
            # Start WebSocket manager
            await ws_manager.start()
            
            # Initialize symbols
            await symbol_manager.initialize_symbols()
            
            # Start WebSocket clients
            for symbol in symbol_manager.get_active_symbols():
                for market_type in system_config.market_types:
                    if symbol_manager.is_symbol_active(symbol, market_type):
                        client = BitgetWebSocketClient(symbol, market_type)
                        self.ws_clients.append(client)
                        asyncio.create_task(client.start())
            
            # Start API server
            api_task = asyncio.create_task(
                uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
            )
            
            logger.info("🎉 Trading system fully operational")
            await self._wait_for_shutdown()
            
        except Exception as e:
            logger.error(f"System startup failed: {e}")
            await self.stop()
            
    async def _wait_for_shutdown(self):
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()
        
        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(sig, stop_event.set)
            
        await stop_event.wait()
        await self.stop()
        
    async def stop(self):
        if not self.running:
            return
            
        self.running = False
        logger.info("Stopping trading system")
        
        # Stop WebSocket clients
        for client in self.ws_clients:
            await client.stop()
            
        # Stop WebSocket manager
        await ws_manager.stop()
        
        logger.info("Trading system stopped")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    
    system = TradingSystem()
    
    try:
        asyncio.run(system.start())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        if system.running:
            asyncio.run(system.stop())
