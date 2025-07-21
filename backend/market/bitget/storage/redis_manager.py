import redis.asyncio as aioredis
import logging
import hashlib
import json
import gzip
import time
from typing import Dict, Any, Optional, List
from market.bitget.config import redis_config, system_config

logger = logging.getLogger("redis-manager")

class RedisConnectionPool:
    """Hochleistungs-Verbindungspool für Redis"""
    
    def __init__(self):
        self._pool = None
        
    async def initialize(self):
        """Initialisiert den Connection Pool"""
        try:
            self._pool = aioredis.ConnectionPool(
                host=redis_config.host,
                port=redis_config.port,
                password=redis_config.password or None,
                max_connections=redis_config.pool_size,
                ssl=redis_config.host not in ['localhost', '127.0.0.1'],
                ssl_cert_reqs='none',
                decode_responses=False
            )
            logger.info(f"✅ Redis pool initialized: {redis_config.host}:{redis_config.port}")
        except Exception as e:
            logger.error(f"❌ Redis init failed: {e}")
            raise
            
    async def get_connection(self):
        """Holt eine Verbindung aus dem Pool"""
        if not self._pool:
            await self.initialize()
        return aioredis.Redis(connection_pool=self._pool)

class RedisManager:
    """Hochleistungs-Manager für Redis-Operationen"""
    
    def __init__(self):
        self._pool = RedisConnectionPool()
        self._dedupe_cache = {}
        self._last_cleanup = time.time()
        
    async def initialize(self):
        """Initialisiert den Manager"""
        await self._pool.initialize()
        logger.info("✅ Redis Manager ready")
        
    async def ping(self) -> bool:
        """Überprüft die Verbindung"""
        try:
            conn = await self._pool.get_connection()
            return await conn.ping()
        except Exception:
            return False
            
    # TRADE OPERATIONS
    
    async def add_trade(self, symbol: str, trade: dict, market_type: str) -> bool:
        """Fügt einen Trade mit Deduplizierung hinzu"""
        try:
            # Deduplizierung
            trade_hash = self._trade_hash(trade)
            if await self._is_duplicate(trade_hash):
                return False
                
            # Stream Key
            stream_key = f"trades:{symbol}:{market_type}"
            
            # Pipeline für höheren Durchsatz
            async with await self._pool.get_connection() as conn:
                async with conn.pipeline(transaction=True) as pipe:
                    pipe.xadd(
                        stream_key,
                        {"data": self._compress(trade)},
                        id=f"{trade['ts']}-0",
                        maxlen=redis_config.stream_maxlen,
                        approximate=True
                    )
                    pipe.setex(
                        f"trade_dedup:{trade_hash}",
                        system_config.deduplication_window,
                        "1"
                    )
                    await pipe.execute()
            
            # Cache für schnellen Zugriff
            self._dedupe_cache[trade_hash] = time.time()
            return True
            
        except Exception as e:
            logger.error(f"❌ Trade add failed: {e}")
            return False
            
    async def get_recent_trades(self, symbol: str, market_type: str, limit: int) -> List[Dict]:
        """Holt die neuesten Trades mit hoher Geschwindigkeit"""
        try:
            stream_key = f"trades:{symbol}:{market_type}"
            async with await self._pool.get_connection() as conn:
                # Holt die letzten 'limit' Einträge
                response = await conn.xrevrange(
                    stream_key, count=limit
                )
                
                # Verarbeitung ohne unnötige Kopien
                trades = []
                for _, data in response:
                    trade_data = self._decompress(data[b"data"])
                    trades.append(trade_data)
                    
                return trades
                
        except Exception as e:
            logger.error(f"❌ Trade fetch failed: {e}")
            return []
    
    # CANDLE OPERATIONS
    
    async def add_candle(self, symbol: str, candle: list, market_type: str) -> bool:
        """Fügt eine Kerze hinzu (hochoptimiert)"""
        try:
            key = f"candle:{symbol}:{market_type}:{candle[0]}"
            data = {
                "o": float(candle[1]),
                "h": float(candle[2]),
                "l": float(candle[3]),
                "c": float(candle[4]),
                "v": float(candle[5]),
                "ts": int(candle[0])
            }
            await (await self._pool.get_connection()).set(
                key, 
                self._compress(data),
                ex=86400  # 24 Stunden TTL
            )
            return True
        except Exception as e:
            logger.error(f"❌ Candle add failed: {e}")
            return False
    
    # INTERNAL UTILS
    
    def _trade_hash(self, trade: dict) -> str:
        """Erzeugt einen eindeutigen Hash für einen Trade"""
        return hashlib.sha256(
            f"{trade['symbol']}:{trade['ts']}:{trade['price']}:{trade['size']}".encode()
        ).hexdigest()
        
    async def _is_duplicate(self, trade_hash: str) -> bool:
        """Prüft auf Duplikate mit Cache-Layer"""
        # In-Memory Cache zuerst
        if trade_hash in self._dedupe_cache:
            return True
            
        # Redis Check
        async with await self._pool.get_connection() as conn:
            exists = await conn.exists(f"trade_dedup:{trade_hash}")
            if exists:
                return True
                
        return False
        
    def _compress(self, data: Any) -> bytes:
        """Kompression mit gzip (schnell und effizient)"""
        return gzip.compress(json.dumps(data).encode())
        
    def _decompress(self, data: bytes) -> Any:
        """Dekomprimiert gzip-komprimierte Daten"""
        return json.loads(gzip.decompress(data).decode())
    
    # MAINTENANCE
    
    async def cleanup_cache(self):
        """Bereinigt den In-Memory Cache regelmäßig"""
        now = time.time()
        if now - self._last_cleanup > 300:  # Alle 5 Minuten
            expired = [k for k, t in self._dedupe_cache.items() if now - t > 600]
            for k in expired:
                del self._dedupe_cache[k]
            self._last_cleanup = now

# Globaler hochleistungsfähiger Manager
redis_manager = RedisManager()