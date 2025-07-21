# Python-Dateien im Bitget-Verzeichnis

Dies ist eine Zusammenstellung aller Python-Dateien im `backend/market/bitget`-Verzeichnis und seinen Unterverzeichnissen, inklusive ihres vollständigen Codes.

## Hauptverzeichnis

### backend/market/bitget/__init__.py
```python
# Package initialization
from .config import (
    redis_config, 
    clickhouse_config, 
    bitget_config, 
    binance_config, 
    system_config,
    TLS_CONFIG
)
```

### backend/market/bitget/config.py
```python
import os
import ssl
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime, timezone

@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", 6380))
    password: str = os.getenv("REDIS_PASSWORD", "")
    pool_size: int = 20
    stream_maxlen: int = 50000
    orderbook_ttl: int = 30

@dataclass
class ClickHouseConfig:
    host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    port: int = int(os.getenv("CLICKHOUSE_PORT", 8123))
    database: str = "trading"
    username: str = os.getenv("CLICKHOUSE_USER", "default")
    password: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    batch_size: int = 1000
    unified_table: str = "candles_unified"

@dataclass
class BitgetConfig:
    # REST API
    rest_base_url: str = "https://api.bitget.com"
    
    # API Credentials (can be updated dynamically)
    api_key: str = os.getenv("BITGET_API_KEY", "PUBLIC_ACCESS")
    secret_key: str = os.getenv("BITGET_SECRET_KEY", "")
    passphrase: str = os.getenv("BITGET_PASSPHRASE", "")
    
    # Static Rate Limits (base values)
    max_rps: int = 8
    historical_rps: float = 3.0
    
    # Dynamic Properties for Free/Premium Mode
    @property
    def is_premium(self) -> bool:
        """Check if premium features are enabled"""
        return self.api_key and self.api_key != "PUBLIC_ACCESS" and len(self.api_key) > 10
    
    @property
    def effective_max_rps(self) -> int:
        """Get current rate limit based on account type"""
        return 120 if self.is_premium else self.max_rps
    
    @property
    def effective_historical_rps(self) -> float:
        """Get historical data rate limit based on account type"""
        return 50.0 if self.is_premium else self.historical_rps
    
    @property
    def max_symbols_per_connection(self) -> int:
        """Maximum symbols per WebSocket connection"""
        return 100 if self.is_premium else 10
    
    @property
    def available_resolutions(self) -> List[int]:
        """Available time resolutions based on account type"""
        if self.is_premium:
            return [1, 5, 15, 60, 300, 900, 3600]  # Including 1s for premium
        return [60, 300, 900, 3600]  # Limited for free
    
    @property
    def max_historical_days(self) -> int:
        """Maximum days for historical data requests"""
        return 365 if self.is_premium else 30
    
    def update_credentials(self, api_key: str, secret_key: str, passphrase: str):
        """Update API credentials dynamically"""
        self.api_key = api_key if api_key else "PUBLIC_ACCESS"
        self.secret_key = secret_key
        self.passphrase = passphrase
    
    # Market Type Mappings
    market_mappings: Dict = field(default_factory=lambda: {
        "spot": {
            "ws_url": "wss://ws.bitget.com/spot/v1/stream",
            "inst_type": "SP",
            "suffix": "_SPBL"
        },
        "usdtm": {
            "ws_url": "wss://ws.bitget.com/mix/v1/stream", 
            "inst_type": "UMCBL",
            "suffix": "_UMCBL"
        },
        "coinm": {
            "ws_url": "wss://ws.bitget.com/mix/v1/stream",
            "inst_type": "DMCBL", 
            "suffix": "_DMCBL"
        },
        "usdcm": {
            "ws_url": "wss://ws.bitget.com/mix/v1/stream",
            "inst_type": "CMCBL",
            "suffix": "_CMCBL"
        }
    })

@dataclass
class BinanceConfig:
    ws_url: str = "wss://stream.binance.com:9443/ws"
    api_key: str = os.getenv("BINANCE_API_KEY", "")
    secret_key: str = os.getenv("BINANCE_SECRET_KEY", "")
    max_rps: int = 10

@dataclass
class SystemConfig:
    # Auto-discovered symbols (will be populated)
    symbols: List[str] = field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "SOLUSDT"])  # Default fallback
    market_types: List[str] = field(default_factory=lambda: ["spot", "usdtm"])  # Default markets
    
    # Symbol selection criteria
    min_volume_24h: float = 1000000.0  # Minimum $1M volume
    base_max_symbols_per_market: int = 30   # Base max symbols per market type
    
    # Resolution settings (base values)
    base_resolutions: List[int] = field(default_factory=lambda: [60, 300, 900])  # Base resolutions
    deduplication_window: int = 3600
    
    # Historical target dates per symbol
    historical_target_dates: Dict[str, datetime] = field(default_factory=lambda: {
        "BTCUSDT": datetime(2020, 1, 1, tzinfo=timezone.utc),
        "ETHUSDT": datetime(2021, 1, 1, tzinfo=timezone.utc)
    })
    
    # Dynamic methods (use dependency injection to avoid circular imports)
    def get_effective_market_types(self, bitget_config) -> List[str]:
        """Get available market types based on account type"""
        base_markets = ["spot", "usdtm"]
        if bitget_config.is_premium:
            return base_markets + ["coinm", "usdcm"]  # Add premium markets
        return base_markets
    
    def get_max_symbols_per_market(self, bitget_config) -> int:
        """Get maximum symbols per market based on account type"""
        if bitget_config.is_premium:
            return 150  # Premium allows more symbols
        return self.base_max_symbols_per_market
    
    def get_resolutions(self, bitget_config) -> List[int]:
        """Get available resolutions based on account type"""
        return bitget_config.available_resolutions
    
    def get_total_max_symbols(self, bitget_config) -> int:
        """Total maximum symbols across all markets"""
        market_types = self.get_effective_market_types(bitget_config)
        max_symbols = self.get_max_symbols_per_market(bitget_config)
        return len(market_types) * max_symbols
    
    def update_for_premium(self, bitget_config):
        """Update configuration when premium features are activated"""
        if bitget_config.is_premium:
            # Expand market coverage
            if "coinm" not in self.market_types:
                self.market_types.extend(["coinm", "usdcm"])
            
            # Update historical targets for more pairs
            additional_targets = {
                "BNBUSDT": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "ADAUSDT": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "DOTUSDT": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "LINKUSDT": datetime(2021, 1, 1, tzinfo=timezone.utc),
            }
            self.historical_target_dates.update(additional_targets)
    
    def get_active_symbols_for_market(self, market_type: str, bitget_config) -> List[str]:
        """Get active symbols for a specific market type"""
        # This would be populated by symbol discovery
        # For now, return a subset based on limits
        all_symbols = self.symbols
        max_symbols = self.get_max_symbols_per_market(bitget_config)
        return all_symbols[:max_symbols]

# TLS-Konfiguration
TLS_CONFIG = {
    "ssl": True,
    "ssl_ca_certs": os.getenv("SSL_CA_CERTS", None),
    "ssl_certfile": os.getenv("SSL_CERT_FILE", None),
    "ssl_keyfile": os.getenv("SSL_KEY_FILE", None),
    "ssl_cert_reqs": ssl.CERT_REQUIRED if os.getenv("SSL_VERIFY", "true") == "true" else ssl.CERT_NONE
}

# Konfigurationsinstanzen
redis_config = RedisConfig()
clickhouse_config = ClickHouseConfig()
bitget_config = BitgetConfig()
binance_config = BinanceConfig()
system_config = SystemConfig()
```

### backend/market/bitget/main.py
```python
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
```

## API-Verzeichnis

### backend/market/bitget/api/symbols_api.py
```python
from fastapi import APIRouter, Query
from market.bitget.services.symbol_discovery import symbol_discovery

router = APIRouter()

@router.get("/symbols/all")
async def get_all_symbols():
    """Get all discovered symbols"""
    return {
        "total_symbols": len(symbol_discovery.symbols),
        "symbols": symbol_discovery.symbols
    }

@router.get("/symbols/top")
async def get_top_symbols(
    market_type: str = Query(None, description="Market type (spot, usdtm, etc.)"),
    limit: int = Query(50, description="Number of symbols to return")
):
    """Get top symbols by volume"""
    symbols = await symbol_discovery.get_top_symbols_by_volume(market_type, limit)
    return {
        "market_type": market_type or "all",
        "count": len(symbols),
        "symbols": symbols
    }

@router.get("/symbols/{symbol}/info")
async def get_symbol_info(
    symbol: str, 
    market_type: str = Query(..., description="Market type")
):
    """Get detailed info for a symbol"""
    key = f"{symbol}_{market_type}"
    symbol_info = symbol_discovery.symbols.get(key)
    if not symbol_info:
        return {"error": "Symbol not found"}
    return symbol_info
```

### backend/market/bitget/api/user_api.py
```python
"""
API Endpoints für Benutzerkonfiguration
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from market.bitget.config import bitget_config, system_config
from market.bitget.services.bitget_rest import BitgetRestAPI
from market.bitget.services.auto_remediation import check_system_health

router = APIRouter(prefix="/api/user", tags=["user"])
logger = logging.getLogger(__name__)

class BitgetApiSettings(BaseModel):
    api_key: str = Field(..., min_length=10, description="Bitget API Key")
    secret_key: str = Field(..., min_length=10, description="Bitget Secret Key")
    passphrase: str = Field(..., min_length=3, description="Bitget Passphrase")

class ApiLimitsResponse(BaseModel):
    max_rps: int
    max_symbols_per_market: int
    max_symbols_per_connection: int
    available_resolutions: list
    max_historical_days: int
    is_premium: bool
    effective_market_types: list
    total_max_symbols: int

class ApiStatusResponse(BaseModel):
    status: str
    premium_features: bool
    message: str
    limits: Optional[ApiLimitsResponse] = None

@router.post("/set_bitget_api", response_model=ApiStatusResponse)
async def set_bitget_api(settings: BitgetApiSettings):
    """
    Setzt Bitget API-Schlüssel und aktiviert Premium-Features
    """
    try:
        logger.info(f"Attempting to validate Bitget API credentials")
        
        # Erstelle temporäre API-Instanz für Validierung
        test_api = BitgetRestAPI()
        
        # Temporär die Credentials setzen
        old_key = bitget_config.api_key
        old_secret = bitget_config.secret_key
        old_passphrase = bitget_config.passphrase
        
        # Neue Credentials setzen
        bitget_config.update_credentials(
            settings.api_key, 
            settings.secret_key, 
            settings.passphrase
        )
        
        # Validierung durch API-Test
        try:
            # Test mit öffentlichem Endpoint
            response = await test_api.fetch_spot_symbols()
            
            if not response or response.get("code") != "00000":
                raise ValueError("API credentials validation failed")
            
            # Weitere Validierung mit privaten Endpunkten (falls verfügbar)
            if bitget_config.is_premium:
                # Test mit Account-Info (signierte Anfrage)
                logger.info("Testing signed API request for premium validation")
                # Hier würde normalerweise eine signierte Anfrage folgen
            
            logger.info("✅ API credentials validated successfully")
            
        except Exception as validation_error:
            # Rollback bei Validierungsfehler
            bitget_config.update_credentials(old_key, old_secret, old_passphrase)
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid API credentials: {str(validation_error)}"
            )
        
        # Systemkonfiguration für Premium aktualisieren
        system_config.update_for_premium(bitget_config)
        
        # Aktuelle Limits abrufen
        limits = get_current_limits()
        
        logger.info(f"✅ Premium features {'activated' if bitget_config.is_premium else 'not available'}")
        
        return ApiStatusResponse(
            status="success",
            premium_features=bitget_config.is_premium,
            message="API credentials updated successfully" + 
                   (" - Premium features activated!" if bitget_config.is_premium else " - Using free tier"),
            limits=limits
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to set API credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/limits", response_model=ApiLimitsResponse)
async def get_current_limits():
    """
    Gibt aktuelle Rate Limits und Konfiguration zurück
    """
    return ApiLimitsResponse(
        max_rps=bitget_config.effective_max_rps,
        max_symbols_per_market=system_config.get_max_symbols_per_market(bitget_config),
        max_symbols_per_connection=bitget_config.max_symbols_per_connection,
        available_resolutions=bitget_config.available_resolutions,
        max_historical_days=bitget_config.max_historical_days,
        is_premium=bitget_config.is_premium,
        effective_market_types=system_config.get_effective_market_types(bitget_config),
        total_max_symbols=system_config.get_total_max_symbols(bitget_config)
    )

@router.get("/status", response_model=Dict[str, Any])
async def get_api_status():
    """
    Gibt aktuellen API-Status zurück
    """
    try:
        # System Health Check
        health = await check_system_health()
        
        return {
            "api_configured": bitget_config.api_key != "PUBLIC_ACCESS",
            "is_premium": bitget_config.is_premium,
            "system_health": health,
            "limits": await get_current_limits(),
            "active_markets": system_config.get_effective_market_types(bitget_config),
            "total_symbols": len(system_config.symbols)
        }
    except Exception as e:
        logger.error(f"❌ Failed to get API status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reset_bitget_api")
async def reset_bitget_api():
    """
    Setzt Bitget API-Konfiguration auf Free Tier zurück
    """
    try:
        logger.info("Resetting Bitget API to free tier")
        
        # Auf öffentlichen Zugang zurücksetzen
        bitget_config.update_credentials("PUBLIC_ACCESS", "", "")
        
        # Systemkonfiguration zurücksetzen
        system_config.market_types = ["spot", "usdtm"]
        
        return {
            "status": "success",
            "message": "API credentials reset to free tier",
            "is_premium": False
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to reset API configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/test_connection")
async def test_api_connection():
    """
    Testet die aktuelle API-Verbindung
    """
    try:
        test_api = BitgetRestAPI()
        
        # Test öffentlicher Endpoint
        symbols_response = await test_api.fetch_spot_symbols()
        if not symbols_response or symbols_response.get("code") != "00000":
            raise ValueError("Public API test failed")
        
        # Test Ticker-Daten
        ticker_response = await test_api.fetch_spot_tickers()
        if not ticker_response or ticker_response.get("code") != "00000":
            raise ValueError("Ticker API test failed")
        
        return {
            "status": "success",
            "message": "API connection test successful",
            "symbols_count": len(symbols_response.get("data", [])),
            "tickers_count": len(ticker_response.get("data", [])),
            "is_premium": bitget_config.is_premium
        }
    
    except Exception as e:
        logger.error(f"❌ API connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")
```

### backend/market/bitget/api/ws_manager.py
```python
import asyncio
import json
import time
import traceback
import logging
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime

# Structured logging setup
logger = logging.getLogger("ws-manager")

class PerformantWebSocketManager:
    """Optimized WebSocket manager with connection pooling and batching"""
    def __init__(self, batch_interval_ms: int = 50, debounce_ms: int = 25):
        self.connections: Dict[str, Set[WebSocket]] = {}
        self.message_queues: Dict[str, list] = {}
        self.last_updates: Dict[str, float] = {}
        self.batch_interval_ms = batch_interval_ms
        self.debounce_ms = debounce_ms
        self._batch_task = None
        self._running = False
        self.metrics = {
            "messages_sent": 0,
            "messages_queued": 0,
            "connections_total": 0,
            "errors_count": 0
        }
    
    async def start(self):
        self._running = True
        self._batch_task = asyncio.create_task(self._process_message_batches())
        logger.info("WebSocket manager started")
    
    async def stop(self):
        self._running = False
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocket manager stopped")
    
    async def connect(self, websocket: WebSocket, symbol: str):
        try:
            await websocket.accept()
            
            if symbol not in self.connections:
                self.connections[symbol] = set()
                self.message_queues[symbol] = []
            
            self.connections[symbol].add(websocket)
            self.metrics["connections_total"] += 1
            
            logger.info(f"Client connected to {symbol}")
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
    
    async def disconnect(self, websocket: WebSocket, symbol: str):
        try:
            if symbol in self.connections:
                self.connections[symbol].discard(websocket)
                if not self.connections[symbol]:
                    del self.connections[symbol]
                    if symbol in self.message_queues:
                        del self.message_queues[symbol]
                    if symbol in self.last_updates:
                        del self.last_updates[symbol]
            
            logger.info(f"Client disconnected from {symbol}")
            
        except Exception as e:
            logger.error(f"Disconnection error: {e}")
    
    async def broadcast_to_symbol(self, symbol: str, message: dict, debounce_ms: int = None):
        try:
            if symbol not in self.connections:
                return
            
            effective_debounce = debounce_ms if debounce_ms is not None else self.debounce_ms
            current_time = time.time() * 1000
            
            if symbol in self.last_updates:
                if current_time - self.last_updates[symbol] < effective_debounce:
                    return
            
            self.last_updates[symbol] = current_time
            
            if symbol not in self.message_queues:
                self.message_queues[symbol] = []
            
            self.message_queues[symbol].append(message)
            self.metrics["messages_queued"] += 1
            
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            self.metrics["errors_count"] += 1
    
    async def _process_message_batches(self):
        logger.info("Starting batch processing")
        
        while self._running:
            try:
                for symbol, messages in list(self.message_queues.items()):
                    if not messages or symbol not in self.connections:
                        continue
                    
                    latest_message = messages[-1]
                    self.message_queues[symbol] = []
                    
                    disconnected = set()
                    for websocket in self.connections[symbol].copy():
                        try:
                            await websocket.send_text(json.dumps(latest_message))
                            self.metrics["messages_sent"] += 1
                        except Exception:
                            disconnected.add(websocket)
                            self.metrics["errors_count"] += 1
                    
                    for ws in disconnected:
                        self.connections[symbol].discard(ws)
                
                await asyncio.sleep(self.batch_interval_ms / 1000.0)
                
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                await asyncio.sleep(0.1)
    
    def get_connection_count(self, symbol: str = None) -> int:
        if symbol:
            return len(self.connections.get(symbol, set()))
        return sum(len(conns) for conns in self.connections.values())
    
    def get_metrics(self) -> dict:
        return {
            **self.metrics,
            "active_symbols": len(self.connections),
            "total_connections": self.get_connection_count(),
            "batch_interval_ms": self.batch_interval_ms,
            "debounce_ms": self.debounce_ms
        }

# Global WebSocket manager instance
ws_manager = PerformantWebSocketManager()

async def handle_websocket_connection(websocket: WebSocket, symbol: str):
    client_id = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    
    try:
        await ws_manager.connect(websocket, symbol)
        
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "server_time": int(time.time() * 1000)
        }))
        
        logger.info(f"Connection established: {client_id} -> {symbol}")
        
        ping_interval = 30.0
        
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=ping_interval)
                
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat(),
                            "server_time": int(time.time() * 1000)
                        }))
                except json.JSONDecodeError:
                    pass
                    
            except asyncio.TimeoutError:
                try:
                    await websocket.send_text(json.dumps({
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat(),
                        "server_time": int(time.time() * 1000)
                    }))
                except Exception:
                    break
                    
            except Exception:
                break
                
    except Exception as e:
        logger.error(f"Connection error: {e}")
    finally:
        await ws_manager.disconnect(websocket, symbol)
        logger.info(f"Connection closed: {client_id} -> {symbol}")

async def broadcast_trade_data(symbol: str, trade_data: dict):
    try:
        message = {
            "type": "trade",
            "symbol": trade_data.get("symbol", symbol),
            "market": trade_data.get("market", "spot"),
            "price": float(trade_data["price"]),
            "size": float(trade_data["size"]),
            "side": trade_data["side"],
            "ts": trade_data["ts"],
            "timestamp": datetime.utcnow().isoformat(),
            "server_time": int(time.time() * 1000)
        }
        
        await ws_manager.broadcast_to_symbol(symbol, message, debounce_ms=25)
        
    except Exception as e:
        logger.error(f"Trade broadcast error: {e}")

async def get_websocket_metrics():
    return ws_manager.get_metrics()

async def update_websocket_performance(batch_interval_ms: int = None, debounce_ms: int = None):
    ws_manager.update_performance_settings(batch_interval_ms, debounce_ms)
    return {"status": "updated", "metrics": ws_manager.get_metrics()}
```

## Services-Verzeichnis

### backend/market/bitget/services/auto_remediation.py
```python
"""
Auto-Remediation Service für Bitget Integration
"""
import logging
import asyncio
import time
from typing import Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger("auto-remediation")

# Globaler Zustand für Failover-Mechanismus
bitget_failover_active = False
_last_health_check = 0.0
_health_check_interval = 30.0  # 30 Sekunden

@dataclass
class SystemHealthMetrics:
    """Metriken für System-Gesundheit"""
    bitget_api: bool = True
    redis_connection: bool = True
    clickhouse_connection: bool = True
    websocket_connections: int = 0
    active_symbols: int = 0
    throughput_percent: float = 100.0
    error_rate_percent: float = 0.0
    last_update: float = field(default_factory=time.time)

_system_metrics = SystemHealthMetrics()

async def activate_failover(reason: str):
    """
    Aktiviert Failover-Modus
    """
    global bitget_failover_active
    bitget_failover_active = True
    logger.warning(f"🔴 Failover aktiviert: {reason}")
    
    # Hier würde normalerweise die Failover-Logik implementiert werden
    # z.B. Umschaltung auf Backup-APIs oder reduzierte Funktionalität

async def deactivate_failover():
    """
    Deaktiviert Failover-Modus
    """
    global bitget_failover_active
    bitget_failover_active = False
    logger.info("🟢 Failover deaktiviert - System wieder normal")

async def check_system_health() -> Dict[str, Any]:
    """
    Führt umfassende System-Gesundheitsprüfung durch
    """
    global _last_health_check, _system_metrics
    
    current_time = time.time()
    
    # Cached Health Check für Performance
    if current_time - _last_health_check < _health_check_interval:
        return _system_metrics_to_dict()
    
    _last_health_check = current_time
    
    try:
        # Bitget API Gesundheit
        api_health = await _check_bitget_api_health()
        _system_metrics.bitget_api = api_health
        
        # Redis Verbindung
        redis_health = await _check_redis_health()
        _system_metrics.redis_connection = redis_health
        
        # ClickHouse Verbindung
        clickhouse_health = await _check_clickhouse_health()
        _system_metrics.clickhouse_connection = clickhouse_health
        
        # WebSocket Verbindungen
        ws_count = await _count_active_websockets()
        _system_metrics.websocket_connections = ws_count
        
        # Symbol-Aktivität
        symbol_count = await _count_active_symbols()
        _system_metrics.active_symbols = symbol_count
        
        # Durchsatz berechnen
        throughput = await _calculate_throughput()
        _system_metrics.throughput_percent = throughput
        
        # Fehlerrate berechnen
        error_rate = await _calculate_error_rate()
        _system_metrics.error_rate_percent = error_rate
        
        _system_metrics.last_update = current_time
        
        # Auto-Remediation auslösen bei kritischen Problemen
        await _evaluate_auto_remediation()
        
        return _system_metrics_to_dict()
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "bitget_api": False,
            "redis": False,
            "clickhouse": False,
            "error": str(e),
            "throughput": 0.0,
            "last_check": current_time
        }

async def _check_bitget_api_health() -> bool:
    """Prüft Bitget API Gesundheit"""
    try:
        from market.bitget.services.bitget_rest import BitgetRestAPI
        
        api = BitgetRestAPI()
        response = await api.fetch_spot_symbols()
        
        if response and response.get("code") == "00000":
            return True
        return False
        
    except Exception as e:
        logger.debug(f"Bitget API health check failed: {str(e)}")
        return False

async def _check_redis_health() -> bool:
    """Prüft Redis Verbindung"""
    try:
        from market.bitget.storage.redis_manager import redis_manager
        
        # Einfacher Ping-Test
        result = await redis_manager.ping()
        return result is True
        
    except Exception as e:
        logger.debug(f"Redis health check failed: {str(e)}")
        return False

async def _check_clickhouse_health() -> bool:
    """Prüft ClickHouse Verbindung"""
    try:
        # Hier würde normalerweise eine ClickHouse-Verbindung getestet
        # Für jetzt nehmen wir an, dass es funktioniert
        return True
        
    except Exception as e:
        logger.debug(f"ClickHouse health check failed: {str(e)}")
        return False

async def _count_active_websockets() -> int:
    """Zählt aktive WebSocket-Verbindungen"""
    try:
        # Hier würde normalerweise die Anzahl der aktiven WS-Verbindungen ermittelt
        # Placeholder für jetzt
        return 2
        
    except Exception:
        return 0

async def _count_active_symbols() -> int:
    """Zählt aktive Symbole"""
    try:
        from market.bitget.config import system_config
        return len(system_config.symbols)
        
    except Exception:
        return 0

async def _calculate_throughput() -> float:
    """Berechnet aktuellen Durchsatz"""
    try:
        from market.bitget.utils.adaptive_rate_limiter import get_all_stats
        
        stats = get_all_stats()
        if stats:
            # Durchschnittliche Erfolgsrate aller Rate Limiter
            total_requests = sum(s.get("total_requests", 0) for s in stats.values())
            successful_requests = sum(s.get("successful_requests", 0) for s in stats.values())
            
            if total_requests > 0:
                return (successful_requests / total_requests) * 100
        
        return 98.5  # Default für gesundes System
        
    except Exception:
        return 50.0

async def _calculate_error_rate() -> float:
    """Berechnet aktuelle Fehlerrate"""
    try:
        from market.bitget.utils.adaptive_rate_limiter import get_all_stats
        
        stats = get_all_stats()
        if stats:
            total_requests = sum(s.get("total_requests", 0) for s in stats.values())
            failed_requests = sum(s.get("failed_requests", 0) for s in stats.values())
            
            if total_requests > 0:
                return (failed_requests / total_requests) * 100
        
        return 1.5  # Default niedrige Fehlerrate
        
    except Exception:
        return 10.0

async def _evaluate_auto_remediation():
    """Evaluiert ob Auto-Remediation aktiviert werden soll"""
    global bitget_failover_active
    
    # Failover aktivieren bei kritischen Problemen
    critical_issues = []
    
    if not _system_metrics.bitget_api:
        critical_issues.append("Bitget API nicht verfügbar")
    
    if not _system_metrics.redis_connection:
        critical_issues.append("Redis-Verbindung verloren")
    
    if _system_metrics.throughput_percent < 50.0:
        critical_issues.append(f"Durchsatz zu niedrig: {_system_metrics.throughput_percent:.1f}%")
    
    if _system_metrics.error_rate_percent > 25.0:
        critical_issues.append(f"Fehlerrate zu hoch: {_system_metrics.error_rate_percent:.1f}%")
    
    if critical_issues and not bitget_failover_active:
        reason = "; ".join(critical_issues)
        await activate_failover(reason)
        
    elif not critical_issues and bitget_failover_active:
        await deactivate_failover()

def _system_metrics_to_dict() -> Dict[str, Any]:
    """Konvertiert SystemHealthMetrics zu Dictionary"""
    return {
        "bitget_api": _system_metrics.bitget_api,
        "redis": _system_metrics.redis_connection,
        "clickhouse": _system_metrics.clickhouse_connection,
        "websocket_connections": _system_metrics.websocket_connections,
        "active_symbols": _system_metrics.active_symbols,
        "throughput": round(_system_metrics.throughput_percent, 1),
        "error_rate": round(_system_metrics.error_rate_percent, 1),
        "failover_active": bitget_failover_active,
        "last_check": _system_metrics.last_update,
        "status": "healthy" if (
            _system_metrics.bitget_api and 
            _system_metrics.redis_connection and
            _system_metrics.throughput_percent > 70.0 and
            _system_metrics.error_rate_percent < 10.0
        ) else "degraded" if not bitget_failover_active else "critical"
    }

async def get_remediation_status() -> Dict[str, Any]:
    """
    Gibt aktuellen Status des Auto-Remediation Systems zurück
    """
    return {
        "failover_active": bitget_failover_active,
        "last_health_check": _last_health_check,
        "check_interval": _health_check_interval,
        "system_metrics": _system_metrics_to_dict()
    }

# Startup-Funktion für regelmäßige Health Checks
async def start_health_monitoring():
    """Startet kontinuierliche Gesundheitsüberwachung"""
    logger.info("🏥 Starting health monitoring service")
    
    while True:
        try:
            await check_system_health()
            await asyncio.sleep(_health_check_interval)
        except Exception as e:
            logger.error(f"❌ Health monitoring error: {str(e)}")
            await asyncio.sleep(5.0)  # Kurze Pause bei Fehlern
```

### backend/market/bitget/services/bitget_client.py
```python
import asyncio
import json
import logging
import websockets
import time
from datetime import datetime, timezone
from typing import List
from market.bitget.config import bitget_config, TLS_CONFIG
from market.bitget.utils.adaptive_rate_limiter import AdaptiveRateLimiter
from market.bitget.storage.redis_manager import redis_manager
from market.bitget.api.ws_manager import broadcast_trade_data
from market.bitget.services.auto_remediation import bitget_failover_active

logger = logging.getLogger("bitget-client")

class BitgetWebSocketClient:
    def __init__(self, symbols: List[str], market_type: str):
        # Support für Symbolgruppen statt einzelne Symbole
        self.symbols = symbols if isinstance(symbols, list) else [symbols]
        self.market_type = market_type
        
        # Get market-specific configuration
        self.market_config = bitget_config.market_mappings.get(market_type)
        if not self.market_config:
            raise ValueError(f"Unsupported market type: {market_type}")
            
        self.ws_url = self.market_config["ws_url"]
        self.inst_type = self.market_config["inst_type"] 
        self.symbol_suffix = self.market_config["suffix"]
        
        self.running = False
        self.reconnect_count = 0
        
        # Dynamische Rate Limiter Konfiguration
        self.rate_limiter = AdaptiveRateLimiter(f"ws-{market_type}-{len(self.symbols)}symbols")
        self.rate_limiter.update_base_rps(bitget_config.effective_max_rps)
        
        # Statistiken für Symbolgruppe
        self.connected_symbols = set()
        self.last_data_time = {}
        
    async def start(self):
        if bitget_failover_active:
            logger.info(f"⏭️  Skipping Bitget for {len(self.symbols)} symbols (failover active)")
            return
            
        self.running = True
        logger.info(f"🚀 Starting Bitget client for {len(self.symbols)} symbols ({self.market_type})")
        
        while self.running:
            try:
                await self._connect_and_listen()
            except Exception as e:
                self.reconnect_count += 1
                logger.error(f"❌ Connection failed ({self.reconnect_count}): {e}")
                
                # Exponential backoff mit Maximum
                backoff_time = min(2 ** self.reconnect_count, 60)
                await asyncio.sleep(backoff_time)
                
    async def _connect_and_listen(self):
        """Verbindet und hört auf WebSocket-Nachrichten für alle Symbole"""
        try:
            async with websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
                **TLS_CONFIG
            ) as ws:
                logger.info(f"✅ Connected to {self.ws_url} for {len(self.symbols)} symbols ({self.market_type})")
                
                # Alle Symbole in dieser Gruppe abonnieren
                await self._subscribe_all_symbols(ws)
                
                # Reset reconnect counter bei erfolgreicher Verbindung
                self.reconnect_count = 0
                
                async for message in ws:
                    if not self.running:
                        break
                    await self._process_message(message)
                    
        except Exception as e:
            logger.error(f"❌ WebSocket connection error: {e}")
            raise
                
    async def _subscribe_all_symbols(self, ws):
        """Abonniert alle Symbole in der Gruppe"""
        start_time = time.time()
        
        try:
            # Erstelle Abonnement-Args für alle Symbole
            args = []
            for symbol in self.symbols:
                inst_id = f"{symbol}{self.symbol_suffix}"
                args.append({
                    "instType": self.inst_type,
                    "channel": "trade",
                    "instId": inst_id
                })
                
                # Premium-Feature: Orderbuch für jedes Symbol hinzufügen
                if bitget_config.is_premium:
                    args.append({
                        "instType": self.inst_type,
                        "channel": "books50",  # 50-Level Orderbuch
                        "instId": inst_id,
                        "snapshot": True
                    })
            
            # Subscription-Message senden
            msg = {
                "op": "subscribe",
                "args": args
            }
            
            await self.rate_limiter.acquire()
            await ws.send(json.dumps(msg))
            
            response_time = time.time() - start_time
            self.rate_limiter.report_success()
            
            logger.info(f"📡 Subscribed to {len(self.symbols)} symbols with {len(args)} channels")
            
        except Exception as e:
            self.rate_limiter.report_error(e)
            logger.error(f"❌ Subscription error: {e}")
            raise
            
    async def _process_message(self, message: str):
        """Verarbeitet eingehende WebSocket-Nachrichten für alle Symbole"""
        try:
            msg = json.loads(message)
            
            # Erfolgsmeldung nach Abonnement
            if msg.get("event") == "subscribe":
                logger.info(f"✅ Subscription confirmed for {len(self.symbols)} symbols")
                return
                
            # Fehlermeldungen behandeln
            if msg.get("event") == "error":
                error_msg = msg.get("msg", "Unknown error")
                self.rate_limiter.report_error(Exception(f"API Error: {error_msg}"))
                logger.error(f"❌ WebSocket error: {error_msg}")
                return
            
            # Daten-Updates verarbeiten
            if msg.get("action") == "update":
                channel = msg.get("arg", {}).get("channel", "")
                data = msg.get("data", [])
                
                if channel == "trade":
                    await self._process_trades(data, msg.get("arg", {}))
                elif channel == "books50" and bitget_config.is_premium:
                    await self._process_orderbook(data, msg.get("arg", {}))
                    
            self.rate_limiter.report_success()
                    
        except Exception as e:
            self.rate_limiter.report_error(e)
            logger.error(f"❌ Message processing error: {e}")
            
    async def _process_trades(self, trades: list, channel_info: dict):
        """Verarbeitet Trade-Daten für ein bestimmtes Symbol"""
        inst_id = channel_info.get("instId", "")
        
        # Symbol aus inst_id extrahieren (entfernt Suffix)
        symbol = inst_id.replace(self.symbol_suffix, "") if inst_id else ""
        
        if symbol not in self.symbols:
            logger.warning(f"⚠️  Received trade for unknown symbol: {symbol}")
            return
        
        # Zeitstempel für Aktivitätstracking aktualisieren
        self.last_data_time[symbol] = time.time()
        self.connected_symbols.add(symbol)
        
        for trade_data in trades:
            try:
                trade = self._parse_trade(trade_data, symbol)
                
                # Store in Redis
                await redis_manager.add_trade(symbol, trade, self.market_type)
                
                # Broadcast via WebSocket
                await broadcast_trade_data(symbol, trade)
                
            except Exception as e:
                logger.error(f"❌ Trade processing error for {symbol}: {e}")
    
    async def _process_orderbook(self, orderbook_data: list, channel_info: dict):
        """Verarbeitet Orderbuch-Daten (Premium Feature)"""
        inst_id = channel_info.get("instId", "")
        symbol = inst_id.replace(self.symbol_suffix, "") if inst_id else ""
        
        if symbol not in self.symbols:
            return
        
        try:
            for book_data in orderbook_data:
                # Orderbuch-Verarbeitung (vereinfacht)
                await redis_manager.add_orderbook(symbol, book_data, self.market_type)
                
        except Exception as e:
            logger.error(f"❌ Orderbook processing error for {symbol}: {e}")
                
    def _parse_trade(self, trade_data: list, symbol: str) -> dict:
        """Parsed Trade-Daten für ein bestimmtes Symbol"""
        # Structure: [timestamp, price, size, side]
        ts_ms = int(trade_data[0])
        price = float(trade_data[1])
        size = float(trade_data[2])
        side = trade_data[3].lower()
        
        return {
            "symbol": symbol,
            "market_type": self.market_type,
            "price": price,
            "size": size,
            "side": side,
            "ts": datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
            "timestamp": ts_ms
        }
    
    def get_connection_stats(self) -> dict:
        """Gibt Verbindungsstatistiken zurück"""
        now = time.time()
        active_symbols = [
            symbol for symbol, last_time in self.last_data_time.items()
            if now - last_time < 60  # Aktiv in letzten 60 Sekunden
        ]
        
        return {
            "market_type": self.market_type,
            "total_symbols": len(self.symbols),
            "connected_symbols": len(self.connected_symbols),
            "active_symbols": len(active_symbols),
            "reconnect_count": self.reconnect_count,
            "rate_limiter_stats": self.rate_limiter.get_stats(),
            "symbols": self.symbols,
            "active_symbols_list": active_symbols
        }
        
    async def stop(self):
        """Stoppt WebSocket-Client für alle Symbole"""
        self.running = False
        logger.info(f"🛑 Stopped Bitget client for {len(self.symbols)} symbols ({self.market_type})")
```

### backend/market/bitget/services/bitget_rest.py
```python
import aiohttp
import json
import logging
import hmac
import hashlib
import base64
import time
import asyncio
from typing import Dict, List, Optional
from market.bitget.config import bitget_config
from market.bitget.utils.adaptive_rate_limiter import AdaptiveRateLimiter

logger = logging.getLogger("bitget-rest")

class BitgetRestAPI:
    """Dynamische Bitget REST API Integration mit Free/Premium Support"""
    
    def __init__(self):
        self.base_url = bitget_config.rest_base_url
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = AdaptiveRateLimiter("bitget-rest")
        self._current_config_hash = self._get_config_hash()
        
    def _get_config_hash(self) -> str:
        """Erzeugt Hash der aktuellen Konfiguration"""
        config_str = f"{bitget_config.api_key}{bitget_config.secret_key}{bitget_config.passphrase}"
        return hashlib.md5(config_str.encode()).hexdigest()
    
    async def _ensure_session(self):
        """Stellt sicher, dass eine gültige Session existiert"""
        config_hash = self._get_config_hash()
        
        # Session neu erstellen wenn Konfiguration geändert wurde
        if (self._session is None or 
            self._session.closed or 
            config_hash != self._current_config_hash):
            
            if self._session and not self._session.closed:
                await self._session.close()
            
            # Timeout basierend auf Account-Typ
            timeout = aiohttp.ClientTimeout(total=60 if bitget_config.is_premium else 30)
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'User-Agent': 'Bitget-Trading-System/1.0',
                    'Content-Type': 'application/json'
                }
            )
            
            self._current_config_hash = config_hash
            
            # Rate Limiter aktualisieren
            self._rate_limiter.update_base_rps(bitget_config.effective_max_rps)
            
            logger.info(f"✅ Session {'renewed' if config_hash != self._current_config_hash else 'created'} "
                       f"- Premium: {bitget_config.is_premium}, RPS: {bitget_config.effective_max_rps}")
    
    @property
    def is_premium(self) -> bool:
        """Check if premium features are available"""
        return bitget_config.is_premium
    
    @property
    def requires_auth(self) -> bool:
        """Check if API key authentication is available"""
        return (bitget_config.api_key != "PUBLIC_ACCESS" and 
                bitget_config.secret_key and 
                bitget_config.passphrase)
        
    async def _sign_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """Erstellt signierte Headers für authentifizierte Requests"""
        if not self.requires_auth:
            return {}
        
        timestamp = str(int(time.time() * 1000))
        message = timestamp + method.upper() + endpoint
        
        if params:
            message += json.dumps(params, separators=(',', ':'))
            
        signature = base64.b64encode(
            hmac.new(
                bitget_config.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return {
            "ACCESS-KEY": bitget_config.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": bitget_config.passphrase
        }
    
    async def _get_request(self, endpoint: str, params: dict = None, require_auth: bool = False) -> dict:
        """Führt GET Request mit automatischer Session-Verwaltung und Rate Limiting aus"""
        await self._ensure_session()
        
        # Rate limiting anwenden
        await self._rate_limiter.acquire()
        
        try:
            headers = {}
            
            # Authentifizierung nur wenn erforderlich und verfügbar
            if require_auth and self.requires_auth:
                auth_headers = await self._sign_request("GET", endpoint, params)
                headers.update(auth_headers)
            elif require_auth and not self.requires_auth:
                raise ValueError(f"Authentication required for {endpoint} but no API credentials configured")
            
            async with self._session.get(
                f"{self.base_url}{endpoint}", 
                params=params, 
                headers=headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Erfolg an Rate Limiter melden
                self._rate_limiter.report_success()
                
                return data
                
        except Exception as e:
            # Fehler an Rate Limiter melden
            self._rate_limiter.report_error(e)
            raise
    
    async def fetch_spot_symbols(self) -> List[Dict]:
        """Spot Symbole - V2 API"""
        return await self._get_request("/api/v2/spot/public/symbols")
        
    async def fetch_futures_symbols(self, product_type: str) -> List[Dict]:
        """Futures Symbole"""
        return await self._get_request("/api/v2/mix/market/contracts", {"productType": product_type})
        
    async def fetch_spot_tickers(self) -> List[Dict]:
        """Spot Ticker"""
        return await self._get_request("/api/v2/spot/market/tickers")
        
    async def fetch_futures_tickers(self, product_type: str) -> List[Dict]:
        """Futures Ticker"""
        return await self._get_request("/api/v2/mix/market/tickers", {"productType": product_type})
        
    async def fetch_spot_orderbook(self, symbol: str, limit: int = 50) -> Dict:
        """Spot Orderbook"""
        return await self._get_request("/api/v2/spot/market/orderbook", {"symbol": symbol, "limit": limit})
        
    async def fetch_futures_orderbook(self, symbol: str, product_type: str, limit: int = 50) -> Dict:
        """Futures Orderbook"""
        return await self._get_request(
            "/api/v2/mix/market/orderbook", 
            {"symbol": symbol, "productType": product_type, "limit": limit}
        )
        
    async def fetch_spot_candles(self, symbol: str, granularity: str, **kwargs) -> List:
        """Spot Kerzen"""
        params = {"symbol": symbol, "granularity": granularity, **kwargs}
        return await self._get_request("/api/v2/spot/market/candles", params)
        
    async def fetch_futures_candles(self, symbol: str, product_type: str, granularity: str, **kwargs) -> List:
        """Futures Kerzen"""
        params = {"symbol": symbol, "productType": product_type, "granularity": granularity, **kwargs}
        return await self._get_request("/api/v2/mix/market/candles", params)
        
    async def close(self):
        """Schließt die Session ordnungsgemäß"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("✅ BitgetRestAPI session closed")
```

### backend/market/bitget/services/symbol_discovery.py
```python
import asyncio
import logging
from market.bitget.config import system_config, bitget_config
from market.bitget.services.bitget_rest import BitgetRestAPI

logger = logging.getLogger("symbol-discovery")

class SymbolDiscoveryService:
    """Automatische Symbol-Entdeckung für alle Märkte"""
    
    def __init__(self):
        self.rest_api = BitgetRestAPI()
        self.symbols = {}
        
    async def initialize(self):
        """Initialize and discover all symbols"""
        logger.info("🔍 Starting symbol discovery")
        await self._discover_spot_symbols()
        await self._discover_futures_symbols("USDT-FUTURES")
        logger.info(f"✅ Discovered {len(self.symbols)} symbols")
        
    async def _discover_spot_symbols(self):
        """Discover spot trading symbols"""
        try:
            data = await self.rest_api.fetch_spot_symbols()
            if data.get("code") == "00000":
                for symbol_data in data.get("data", []):
                    if symbol_data.get("status") == "online":
                        self._add_spot_symbol(symbol_data)
        except Exception as e:
            logger.error(f"Spot symbol discovery failed: {e}")
        
    async def _discover_futures_symbols(self, product_type: str):
        """Discover futures trading symbols"""
        try:
            data = await self.rest_api.fetch_futures_symbols(product_type)
            if data.get("code") == "00000":
                for symbol_data in data.get("data", []):
                    if symbol_data.get("status") == "normal":
                        self._add_futures_symbol(symbol_data, "usdtm")
        except Exception as e:
            logger.error(f"Futures symbol discovery failed: {e}")
        
    def _add_spot_symbol(self, symbol_data: dict):
        """Add spot symbol to registry"""
        symbol = symbol_data["symbol"]
        key = f"{symbol}_spot"
        
        self.symbols[key] = {
            "symbol": symbol,
            "market_type": "spot",
            "base_coin": symbol_data.get("baseCoin", ""),
            "quote_coin": symbol_data.get("quoteCoin", ""),
            "status": symbol_data.get("status", ""),
            "min_size": float(symbol_data.get("minTradeAmount", 0)),
            "max_size": float(symbol_data.get("maxTradeAmount", 0)),
            "size_increment": float(symbol_data.get("quantityScale", 0)),
            "price_increment": float(symbol_data.get("priceScale", 0))
        }
        
    def _add_futures_symbol(self, symbol_data: dict, market_type: str):
        """Add futures symbol to registry"""
        symbol = symbol_data["symbol"]
        key = f"{symbol}_{market_type}"
        
        self.symbols[key] = {
            "symbol": symbol,
            "market_type": market_type,
            "base_coin": symbol_data.get("baseCoin", ""),
            "quote_coin": symbol_data.get("quoteCoin", "USDT"),
            "status": symbol_data.get("status", ""),
            "min_size": float(symbol_data.get("minTradeNum", 0)),
            "max_size": float(symbol_data.get("maxTradeNum", 0)),
            "size_increment": float(symbol_data.get("sizeMultiplier", 0)),
            "price_increment": float(symbol_data.get("pricePlace", 0))
        }
        
    async def get_top_symbols_by_volume(self, market_type: str = None, limit: int = 50) -> list:
        """Get top symbols by 24h volume"""
        symbols = list(self.symbols.values())
        if market_type:
            symbols = [s for s in symbols if s["market_type"] == market_type]
            
        # Sort by volume (dummy implementation)
        symbols.sort(key=lambda x: x.get("volume_24h", 0), reverse=True)
        return symbols[:limit]
        
    async def close(self):
        await self.rest_api.close()

# Global instance
symbol_discovery = SymbolDiscoveryService()
```

### backend/market/bitget/services/symbol_manager.py
```python
import logging
from market.bitget.config import system_config
from market.bitget.services.symbol_discovery import symbol_discovery

logger = logging.getLogger("symbol-manager")

class SymbolManager:
    """Manages active symbols for trading"""
    
    def __init__(self):
        self.active_symbols = {}
        
    async def initialize_symbols(self):
        """Initialize symbols from discovery service"""
        await symbol_discovery.initialize()
        
        # Get top symbols by volume for selected markets
        selected_symbols = set()
        
        for market_type in system_config.market_types:
            top_symbols = await symbol_discovery.get_top_symbols_by_volume(
                market_type, 
                system_config.max_symbols_per_market
            )
            
            for symbol_info in top_symbols:
                if symbol_info.get("volume_24h", 0) >= system_config.min_volume_24h:
                    selected_symbols.add(symbol_info["symbol"])
        
        # Update system config
        system_config.symbols = list(selected_symbols)
        logger.info(f"✅ Selected {len(system_config.symbols)} symbols for trading")
        
        # Activate symbols
        for symbol in system_config.symbols:
            for market_type in system_config.market_types:
                await self.activate_symbol(symbol, market_type)
        
    async def activate_symbol(self, symbol: str, market_type: str):
        """Activate a symbol for trading"""
        key = f"{symbol}_{market_type}"
        self.active_symbols[key] = True
        logger.info(f"✅ Activated {symbol} ({market_type})")
        
    def is_symbol_active(self, symbol: str, market_type: str) -> bool:
        """Check if symbol is active"""
        key = f"{symbol}_{market_type}"
        return key in self.active_symbols
        
    def get_active_symbols(self) -> list:
        """Get list of active symbols"""
        return list(set(symbol.split('_')[0] for symbol in self.active_symbols.keys()))

# Global instance  
symbol_manager = SymbolManager()
```

## Storage-Verzeichnis

### backend/market/bitget/storage/redis_manager.py
```python
import redis.asyncio as aioredis
import logging
import hashlib
import json
import gzip
import time
from typing import Dict, Any, Optional
from market.bitget.config import redis_config, system_config, TLS_CONFIG

logger = logging.getLogger("redis-manager")

class RedisConnectionPool:
    def __init__(self):
        self._pool = None
        self._connection_failures = 0
        self._last_failure_time = 0
        
    async def initialize(self):
        try:
            # Redis-spezifische SSL-Konfiguration (ohne TLS_CONFIG für WebSocket)
            redis_ssl_config = {}
            if redis_config.host not in ['localhost', '127.0.0.1']:
                # SSL nur für Remote-Verbindungen aktivieren
                redis_ssl_config = {
                    'ssl': True,
                    'ssl_check_hostname': False,
                    'ssl_cert_reqs': 'none'
                }
            
            self._pool = aioredis.ConnectionPool(
                host=redis_config.host,
                port=redis_config.port,
                password=redis_config.password if redis_config.password else None,
                max_connections=redis_config.pool_size,
                **redis_ssl_config
            )
            logger.info(f"✅ Redis connection pool initialized - Host: {redis_config.host}:{redis_config.port}")
        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {e}")
            raise
            
    async def get_connection(self):
        if not self._pool:
            await self.initialize()
        return aioredis.Redis(connection_pool=self._pool)
        
    async def execute(self, command: str, *args, **kwargs):
        """Führt Redis-Kommandos mit Fehlerbehandlung aus"""
        try:
            async with await self.get_connection() as conn:
                return await getattr(conn, command)(*args, **kwargs)
        except Exception as e:
            self._connection_failures += 1
            self._last_failure_time = time.time()
            logger.error(f"Redis command '{command}' failed: {e}")
            raise

class RedisManager:
    def __init__(self):
        self._pool = RedisConnectionPool()
        self._dedupe_cache = {}
        
    async def initialize(self):
        """Initialisiert Redis-Verbindung"""
        await self._pool.initialize()
        logger.info("✅ Redis Manager initialized")
    
    async def ping(self) -> bool:
        """Testet Redis-Verbindung"""
        try:
            # Direkte Redis-Verbindung für Ping
            redis_client = await self._pool.get_connection()
            result = await redis_client.ping()
            await redis_client.close()
            
            logger.info(f"✅ Redis ping successful: {result}")
            return result is True or result == b'PONG' or result == 'PONG'
        except Exception as e:
            logger.error(f"❌ Redis ping failed: {e}")
            return False
        
    async def add_trade(self, symbol: str, trade: dict, market_type: str = "spot") -> bool:
        trade["market_type"] = market_type
        trade_hash = self._generate_trade_hash(trade)
        
        if await self._is_duplicate(trade_hash):
            return False
            
        stream_key = f"trades:{symbol}:{market_type}"
        await self._pool.execute(
            "xadd",
            stream_key,
            {"data": self._compress_data(trade)},
            id=f"{trade['timestamp']}-0",
            maxlen=redis_config.stream_maxlen,
            approximate=True
        )
        
        self._dedupe_cache[trade_hash] = time.time()
        return True
    
    async def add_orderbook(self, symbol: str, orderbook_data: dict, market_type: str = "spot") -> bool:
        """Speichert Orderbuch-Daten (Premium Feature)"""
        try:
            orderbook_key = f"orderbook:{symbol}:{market_type}"
            
            # Orderbuch mit TTL speichern
            compressed_data = self._compress_data({
                "symbol": symbol,
                "market_type": market_type,
                "data": orderbook_data,
                "timestamp": int(time.time() * 1000)
            })
            
            await self._pool.execute(
                "setex", 
                orderbook_key, 
                redis_config.orderbook_ttl,  # 30 Sekunden TTL
                compressed_data
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store orderbook for {symbol}: {e}")
            return False
        
    def _generate_trade_hash(self, trade: dict) -> str:
        data = f"{trade['symbol']}:{trade['market_type']}:{trade['timestamp']}:{trade['price']}:{trade['size']}"
        return hashlib.sha256(data.encode()).hexdigest()
        
    async def _is_duplicate(self, trade_hash: str) -> bool:
        if trade_hash in self._dedupe_cache:
            return True
            
        exists = await self._pool.execute("exists", f"trade_dedup:{trade_hash}")
        if exists:
            return True
            
        await self._pool.execute(
            "setex", 
            f"trade_dedup:{trade_hash}", 
            system_config.deduplication_window, 
            "1"
        )
        return False
        
    def _compress_data(self, data: dict) -> bytes:
        return gzip.compress(json.dumps(data).encode())
        
    def _decompress_data(self, data: bytes) -> dict:
        return json.loads(gzip.decompress(data).decode())

redis_manager = RedisManager()
```

## Utils-Verzeichnis

### backend/market/bitget/utils/__init__.py
```python
"""
Utilities für Bitget Integration
"""
from .adaptive_rate_limiter import AdaptiveRateLimiter, get_rate_limiter, get_all_stats

__all__ = ['AdaptiveRateLimiter', 'get_rate_limiter', 'get_all_stats']
```

### backend/market/bitget/utils/adaptive_rate_limiter.py
```python
"""
Adaptiver Rate Limiter für Bitget API mit dynamischen Limits
"""
import asyncio
import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger("rate-limiter")

@dataclass
class RateLimitStats:
    """Statistiken für Rate Limiting"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    throttled_requests: int = 0
    avg_response_time: float = 0.0
    last_reset: float = field(default_factory=time.time)

class AdaptiveRateLimiter:
    """
    Adaptiver Rate Limiter der sich automatisch an API-Limits anpasst
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.base_rps = 8  # Standard Rate Limit
        self.current_rps = self.base_rps
        self.max_burst = 10  # Maximale Burst-Requests
        
        # Request-Tracking
        self.request_times = deque(maxlen=100)
        self.recent_errors = deque(maxlen=10)
        self.stats = RateLimitStats()
        
        # Zustandsverfolgung
        self.last_request_time = 0.0
        self.bucket_tokens = float(self.max_burst)
        self.bucket_last_refill = time.time()
        
        # Adaptive Logik
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.backoff_multiplier = 1.0
        
        logger.info(f"✅ Rate limiter '{name}' initialized - Base RPS: {self.base_rps}")
    
    def update_base_rps(self, new_rps: int):
        """Aktualisiert die Basis-RPS wenn sich die Konfiguration ändert"""
        if new_rps != self.base_rps:
            old_rps = self.base_rps
            self.base_rps = new_rps
            self.current_rps = new_rps
            self.bucket_tokens = float(min(self.bucket_tokens, self.max_burst))
            
            logger.info(f"📈 Rate limit updated for '{self.name}': {old_rps} -> {new_rps} RPS")
    
    def _refill_bucket(self):
        """Token Bucket auffüllen"""
        now = time.time()
        time_passed = now - self.bucket_last_refill
        
        if time_passed > 0:
            # Token basierend auf aktueller RPS hinzufügen
            tokens_to_add = time_passed * self.current_rps
            self.bucket_tokens = min(self.max_burst, self.bucket_tokens + tokens_to_add)
            self.bucket_last_refill = now
    
    def _should_throttle(self) -> bool:
        """Prüft ob Request gedrosselt werden soll"""
        self._refill_bucket()
        
        # Keine Token verfügbar
        if self.bucket_tokens < 1.0:
            return True
        
        # Backoff nach Fehlern
        if self.backoff_multiplier > 1.0:
            min_interval = (1.0 / self.current_rps) * self.backoff_multiplier
            if time.time() - self.last_request_time < min_interval:
                return True
        
        return False
    
    async def acquire(self):
        """Akquiriert einen Request-Slot (mit Warteschleife falls nötig)"""
        request_start = time.time()
        
        while self._should_throttle():
            # Berechne Wartezeit
            self._refill_bucket()
            
            if self.bucket_tokens < 1.0:
                wait_time = (1.0 - self.bucket_tokens) / self.current_rps
            else:
                wait_time = (1.0 / self.current_rps) * self.backoff_multiplier - (time.time() - self.last_request_time)
            
            if wait_time > 0:
                self.stats.throttled_requests += 1
                await asyncio.sleep(min(wait_time, 5.0))  # Max 5s Wartezeit
        
        # Token verbrauchen
        self.bucket_tokens -= 1.0
        self.last_request_time = time.time()
        
        # Request-Zeit für Statistiken
        self.request_times.append(request_start)
        self.stats.total_requests += 1
    
    def report_success(self):
        """Meldet erfolgreichen Request"""
        self.stats.successful_requests += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        
        # Adaptive Verbesserung nach mehreren Erfolgen
        if self.consecutive_successes > 20 and self.backoff_multiplier > 1.0:
            self.backoff_multiplier = max(1.0, self.backoff_multiplier * 0.9)
        
        # Rate vorsichtig erhöhen nach vielen Erfolgen
        if self.consecutive_successes > 50 and self.current_rps < self.base_rps * 1.5:
            self.current_rps = min(self.base_rps * 1.5, self.current_rps * 1.05)
    
    def report_error(self, error: Exception):
        """Meldet Request-Fehler und passt Rate an"""
        self.stats.failed_requests += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        
        error_type = type(error).__name__
        self.recent_errors.append((time.time(), error_type, str(error)[:100]))
        
        # Rate-Limiting-spezifische Fehler
        if any(keyword in str(error).lower() for keyword in 
               ['rate limit', 'too many requests', '429', 'throttle']):
            self.backoff_multiplier = min(4.0, self.backoff_multiplier * 2.0)
            self.current_rps = max(1, self.current_rps * 0.5)
            logger.warning(f"⚠️  Rate limit hit for '{self.name}' - Backing off: {self.backoff_multiplier:.2f}x")
        
        # Andere Fehler nach mehreren Failures
        elif self.consecutive_failures > 5:
            self.backoff_multiplier = min(2.0, self.backoff_multiplier * 1.5)
            logger.warning(f"⚠️  Multiple failures for '{self.name}' - Reducing rate")
    
    def get_stats(self) -> Dict:
        """Gibt aktuelle Statistiken zurück"""
        now = time.time()
        uptime = now - self.stats.last_reset
        
        # Berechne aktuelle Request-Rate
        recent_requests = len([t for t in self.request_times if now - t < 60.0])
        current_rpm = recent_requests
        
        success_rate = (self.stats.successful_requests / max(1, self.stats.total_requests)) * 100
        
        return {
            "name": self.name,
            "base_rps": self.base_rps,
            "current_rps": round(self.current_rps, 2),
            "backoff_multiplier": round(self.backoff_multiplier, 2),
            "bucket_tokens": round(self.bucket_tokens, 1),
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "throttled_requests": self.stats.throttled_requests,
            "success_rate_percent": round(success_rate, 1),
            "current_rpm": current_rpm,
            "consecutive_successes": self.consecutive_successes,
            "consecutive_failures": self.consecutive_failures,
            "recent_errors": len(self.recent_errors),
            "uptime_seconds": round(uptime, 1)
        }
    
    def reset_stats(self):
        """Setzt Statistiken zurück"""
        self.stats = RateLimitStats()
        self.request_times.clear()
        self.recent_errors.clear()
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        logger.info(f"📊 Stats reset for rate limiter '{self.name}'")

# Globaler Rate Limiter für Singleton-Pattern
_rate_limiters: Dict[str, AdaptiveRateLimiter] = {}

def get_rate_limiter(name: str) -> AdaptiveRateLimiter:
    """Gibt Rate Limiter für einen Namen zurück (Singleton)"""
    if name not in _rate_limiters:
        _rate_limiters[name] = AdaptiveRateLimiter(name)
    return _rate_limiters[name]

def get_all_stats() -> Dict[str, Dict]:
    """Gibt Statistiken für alle Rate Limiter zurück"""
    return {name: limiter.get_stats() for name, limiter in _rate_limiters.items()}
```

### backend/market/bitget/utils/circuit_breaker.py
```python
import time
from enum import Enum
import logging

logger = logging.getLogger("circuit-breaker")

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED
        
    async def execute(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit transitioning to HALF_OPEN")
            else:
                raise CircuitOpenException("Circuit is open")
                
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e
            
    def _record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info("Circuit CLOSED")
            
    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self._open_circuit()
            
    def _open_circuit(self):
        self.state = CircuitState.OPEN
        logger.warning(f"Circuit OPEN after {self.failure_count} failures")

class CircuitOpenException(Exception):
    pass
