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
