import asyncio
import signal
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
from market.bitget.api.user_api import router as user_router
from market.bitget.services.auto_remediation import start_health_monitoring

logger = logging.getLogger("trading-system")

# FastAPI App mit CORS für Frontend-Integration
app = FastAPI(
    title="Bitget Trading System API",
    description="Dynamische Bitget Integration mit Free/Premium-Unterstützung",
    version="1.0.0"
)

# CORS für Frontend-Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion spezifischer setzen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router registrieren
app.include_router(symbols_router, prefix="/api")
app.include_router(user_router)  # User API mit eigenem Prefix

class TradingSystem:
    def __init__(self):
        self.ws_clients = []
        self.running = False
        self.health_monitor_task = None
        self.current_config_hash = None
        
    async def start(self):
        self.running = True
        
        try:
            logger.info(f"🚀 Starting Bitget Trading System - Premium: {bitget_config.is_premium}")
            
            # Initialize Redis
            await redis_manager.initialize()
            
            # Start WebSocket manager
            await ws_manager.start()
            
            # Initialize symbols
            await symbol_manager.initialize_symbols()
            
            # Start WebSocket clients with dynamic grouping
            await self._initialize_websocket_clients()
            
            # Start health monitoring
            self.health_monitor_task = asyncio.create_task(start_health_monitoring())
            
            # Start API server
            config = uvicorn.Config(
                app, 
                host="0.0.0.0", 
                port=8000, 
                log_level="info",
                access_log=False  # Reduziert Logs für bessere Performance
            )
            server = uvicorn.Server(config)
            api_task = asyncio.create_task(server.serve())
            
            logger.info(f"🎉 Trading system fully operational")
            logger.info(f"📊 Active markets: {system_config.get_effective_market_types(bitget_config)}")
            logger.info(f"📈 Max symbols per market: {system_config.get_max_symbols_per_market(bitget_config)}")
            logger.info(f"⏱️  Available resolutions: {bitget_config.available_resolutions}")
            
            await self._wait_for_shutdown()
            
        except Exception as e:
            logger.error(f"❌ System startup failed: {e}")
            await self.stop()
    
    async def _initialize_websocket_clients(self):
        """Initialisiert WebSocket-Clients basierend auf aktueller Konfiguration"""
        effective_markets = system_config.get_effective_market_types(bitget_config)
        max_symbols_per_connection = bitget_config.max_symbols_per_connection
        
        logger.info(f"🔌 Initializing WebSocket clients - Max {max_symbols_per_connection} symbols per connection")
        
        for market_type in effective_markets:
            # Aktive Symbole für diesen Markt abrufen
            active_symbols = system_config.get_active_symbols_for_market(market_type, bitget_config)
            
            # Symbole in Gruppen aufteilen
            symbol_groups = [
                active_symbols[i:i + max_symbols_per_connection] 
                for i in range(0, len(active_symbols), max_symbols_per_connection)
            ]
            
            logger.info(f"📊 Market {market_type}: {len(active_symbols)} symbols in {len(symbol_groups)} connections")
            
            # WebSocket-Client für jede Symbolgruppe erstellen
            for group_index, symbol_group in enumerate(symbol_groups):
                if symbol_group:  # Nur wenn Gruppe nicht leer ist
                    client = BitgetWebSocketClient(symbol_group, market_type)
                    self.ws_clients.append(client)
                    
                    # Client asynchron starten
                    client_task = asyncio.create_task(client.start())
                    # Task-Name für besseres Debugging
                    client_task.set_name(f"ws-{market_type}-group-{group_index}")
        
        logger.info(f"✅ Initialized {len(self.ws_clients)} WebSocket clients")
    
    async def _reconfigure_on_api_change(self):
        """Rekonfiguriert System nach API-Schlüssel-Änderung"""
        config_hash = f"{bitget_config.api_key}{bitget_config.is_premium}"
        
        if config_hash != self.current_config_hash:
            logger.info("🔄 API configuration changed - Reinitializing system")
            
            # Bestehende WebSocket-Clients stoppen
            for client in self.ws_clients:
                try:
                    await client.stop()
                except Exception as e:
                    logger.warning(f"⚠️  Error stopping WS client: {e}")
            
            self.ws_clients.clear()
            
            # System-Konfiguration für Premium aktualisieren
            system_config.update_for_premium(bitget_config)
            
            # Neue WebSocket-Clients initialisieren
            await self._initialize_websocket_clients()
            
            self.current_config_hash = config_hash
            logger.info("✅ System reconfiguration completed")
            
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
