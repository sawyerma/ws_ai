import asyncio
import json
import time
import traceback
import logging
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime

# Structured logging setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

class PerformantWebSocketManager:
    """
    Optimized WebSocket manager with connection pooling, message batching,
    and comprehensive error logging
    """
    def __init__(self, batch_interval_ms: int = 50, debounce_ms: int = 25):
        # Connection pools per symbol
        self.connections: Dict[str, Set[WebSocket]] = {}
        # Message queues for batching
        self.message_queues: Dict[str, list] = {}
        # Last update timestamps for debouncing
        self.last_updates: Dict[str, float] = {}
        # Configurable intervals for performance tuning
        self.batch_interval_ms = batch_interval_ms
        self.debounce_ms = debounce_ms
        # Batch processing task
        self._batch_task = None
        self._running = False
        # Performance metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_queued": 0,
            "connections_total": 0,
            "errors_count": 0
        }
    
    async def start(self):
        """Start the batch processing task"""
        self._running = True
        self._batch_task = asyncio.create_task(self._process_message_batches())
        logger.info(f"WebSocket manager started with batch_interval={self.batch_interval_ms}ms, debounce={self.debounce_ms}ms")
    
    async def stop(self):
        """Stop the batch processing task"""
        self._running = False
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocket manager stopped")
    
    def update_performance_settings(self, batch_interval_ms: int = None, debounce_ms: int = None):
        """
        Dynamically update performance settings for live tuning
        """
        if batch_interval_ms is not None:
            self.batch_interval_ms = batch_interval_ms
            logger.info(f"Updated batch_interval to {batch_interval_ms}ms")
        
        if debounce_ms is not None:
            self.debounce_ms = debounce_ms
            logger.info(f"Updated debounce to {debounce_ms}ms")
    
    async def connect(self, websocket: WebSocket, symbol: str):
        """Connect a WebSocket to a symbol channel"""
        try:
            await websocket.accept()
            
            if symbol not in self.connections:
                self.connections[symbol] = set()
                self.message_queues[symbol] = []
            
            self.connections[symbol].add(websocket)
            self.metrics["connections_total"] += 1
            
            logger.info(f"Client connected to {symbol}. Symbol connections: {len(self.connections[symbol])}, Total: {self.get_connection_count()}")
            
        except Exception as e:
            logger.error(f"Error connecting client to {symbol}: {e}")
            traceback.print_exc()
            raise
    
    async def disconnect(self, websocket: WebSocket, symbol: str):
        """Disconnect a WebSocket from a symbol channel"""
        try:
            if symbol in self.connections:
                self.connections[symbol].discard(websocket)
                if not self.connections[symbol]:
                    # Clean up empty channels
                    del self.connections[symbol]
                    if symbol in self.message_queues:
                        del self.message_queues[symbol]
                    if symbol in self.last_updates:
                        del self.last_updates[symbol]
                    logger.info(f"Cleaned up empty channel for {symbol}")
            
            logger.info(f"Client disconnected from {symbol}. Total connections: {self.get_connection_count()}")
            
        except Exception as e:
            logger.error(f"Error disconnecting client from {symbol}: {e}")
            traceback.print_exc()
    
    async def broadcast_to_symbol(self, symbol: str, message: dict, debounce_ms: int = None):
        """
        Broadcast message to all connections for a symbol with configurable debouncing
        """
        try:
            if symbol not in self.connections or not self.connections[symbol]:
                return
            
            # Use instance debounce or override
            effective_debounce = debounce_ms if debounce_ms is not None else self.debounce_ms
            current_time = time.time() * 1000  # Convert to milliseconds
            
            # Debouncing: Skip if last update was too recent
            if symbol in self.last_updates:
                if current_time - self.last_updates[symbol] < effective_debounce:
                    return
            
            self.last_updates[symbol] = current_time
            
            # Add message to batch queue
            if symbol not in self.message_queues:
                self.message_queues[symbol] = []
            
            self.message_queues[symbol].append(message)
            self.metrics["messages_queued"] += 1
            
        except Exception as e:
            logger.error(f"Error broadcasting to {symbol}: {e}")
            traceback.print_exc()
            self.metrics["errors_count"] += 1
    
    async def _process_message_batches(self):
        """
        Process message batches with configurable interval for optimal performance
        """
        logger.info("Started message batch processing")
        
        while self._running:
            try:
                batch_start = time.time()
                messages_processed = 0
                
                # Process all queued messages
                for symbol, messages in list(self.message_queues.items()):
                    if not messages or symbol not in self.connections:
                        continue
                    
                    # Get the latest message (most recent data) - FLAT STRUCTURE
                    latest_message = messages[-1]
                    
                    # Clear the queue
                    self.message_queues[symbol] = []
                    
                    # Broadcast to all connections for this symbol
                    disconnected = set()
                    for websocket in self.connections[symbol].copy():
                        try:
                            await websocket.send_text(json.dumps(latest_message))
                            self.metrics["messages_sent"] += 1
                            messages_processed += 1
                        except Exception as e:
                            logger.warning(f"Error sending to client on {symbol}: {e}")
                            disconnected.add(websocket)
                            self.metrics["errors_count"] += 1
                    
                    # Remove disconnected clients
                    for ws in disconnected:
                        self.connections[symbol].discard(ws)
                        if disconnected:
                            logger.info(f"Removed {len(disconnected)} disconnected clients from {symbol}")
                
                # Performance logging every 1000 batches
                if self.metrics["messages_sent"] % 1000 == 0 and messages_processed > 0:
                    batch_time = (time.time() - batch_start) * 1000
                    logger.info(f"Batch processed: {messages_processed} messages in {batch_time:.2f}ms. Total sent: {self.metrics['messages_sent']}")
                
                # Wait for next batch (configurable interval)
                await asyncio.sleep(self.batch_interval_ms / 1000.0)
                
            except Exception as e:
                logger.error(f"Error in batch processing: {e}")
                traceback.print_exc()
                self.metrics["errors_count"] += 1
                await asyncio.sleep(0.1)  # Fallback delay
    
    def get_connection_count(self, symbol: str = None) -> int:
        """Get total connection count or for specific symbol"""
        if symbol:
            return len(self.connections.get(symbol, set()))
        return sum(len(conns) for conns in self.connections.values())
    
    def get_metrics(self) -> dict:
        """Get performance metrics for monitoring"""
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
    """
    Handle individual WebSocket connection with comprehensive error handling
    """
    client_id = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    
    try:
        await ws_manager.connect(websocket, symbol)
        
        # Send initial connection confirmation - FLAT STRUCTURE
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "server_time": int(time.time() * 1000)
        }))
        
        logger.info(f"WebSocket connection established: {client_id} -> {symbol}")
        
        # Keep connection alive with configurable ping interval
        ping_interval = 30.0  # seconds
        
        while True:
            try:
                # Wait for messages from client (ping/pong, etc.)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=ping_interval)
                
                # Handle client messages if needed
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat(),
                            "server_time": int(time.time() * 1000)
                        }))
                    elif data.get("type") == "subscribe":
                        # Handle additional subscriptions
                        logger.info(f"Client {client_id} subscription request: {data}")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from client {client_id}: {e}")
                    
            except asyncio.TimeoutError:
                # Send periodic ping to keep connection alive
                try:
                    await websocket.send_text(json.dumps({
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat(),
                        "server_time": int(time.time() * 1000)
                    }))
                except Exception as ping_error:
                    logger.error(f"Failed to send ping to {client_id}: {ping_error}")
                    break
                    
            except Exception as e:
                logger.error(f"Connection error for {client_id} on {symbol}: {e}")
                traceback.print_exc()
                break
                
    except Exception as e:
        logger.error(f"WebSocket error for {client_id} on {symbol}: {e}")
        traceback.print_exc()
    finally:
        await ws_manager.disconnect(websocket, symbol)
        logger.info(f"WebSocket connection closed: {client_id} -> {symbol}")

# FLAT STRUCTURE - Keine Verschachtelung in "data"
async def broadcast_trade_data(symbol: str, trade_data: dict):
    """
    Broadcast trade data to connected clients - FLAT STRUCTURE
    """
    try:
        # FLAT STRUCTURE: Alle Felder auf oberster Ebene
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
        logger.error(f"Error broadcasting trade data for {symbol}: {e}")
        traceback.print_exc()

async def broadcast_candle_data(symbol: str, candle_data: dict):
    """
    Broadcast candle data to connected clients - FLAT STRUCTURE
    """
    try:
        # FLAT STRUCTURE: Alle Felder auf oberster Ebene
        message = {
            "type": "candle",
            "symbol": candle_data.get("symbol", symbol),
            "market": candle_data.get("market", "spot"),
            "open": float(candle_data["open"]),
            "high": float(candle_data["high"]),
            "low": float(candle_data["low"]),
            "close": float(candle_data["close"]),
            "volume": float(candle_data["volume"]),
            "ts": candle_data["ts"],
            "timestamp": datetime.utcnow().isoformat(),
            "server_time": int(time.time() * 1000)
        }
        
        await ws_manager.broadcast_to_symbol(symbol, message, debounce_ms=100)
        
    except Exception as e:
        logger.error(f"Error broadcasting candle data for {symbol}: {e}")
        traceback.print_exc()

# Performance monitoring endpoint
async def get_websocket_metrics():
    """Get WebSocket performance metrics"""
    return ws_manager.get_metrics()

# Dynamic performance tuning endpoint
async def update_websocket_performance(batch_interval_ms: int = None, debounce_ms: int = None):
    """Update WebSocket performance settings dynamically"""
    ws_manager.update_performance_settings(batch_interval_ms, debounce_ms)
    return {"status": "updated", "metrics": ws_manager.get_metrics()}
