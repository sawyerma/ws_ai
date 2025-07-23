# backend/core/services/aggregator.py
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models.trade import UnifiedTrade

logger = logging.getLogger("candle-aggregator")

class UnifiedCandleAggregator:
    def __init__(self, resolution: int):
        self.resolution = resolution  # Auflösung in Sekunden
        self.candles: Dict[str, dict] = {}
        self.cache_ttl = timedelta(minutes=15)
        logger.info(f"Initialized aggregator for {resolution}s resolution")

    def _candle_key(self, trade: UnifiedTrade) -> str:
        """Erstellt eindeutigen Key für Candle basierend auf Exchange/Symbol/Market"""
        return f"{trade.exchange}:{trade.symbol}:{trade.market.value}"

    def process_trade(self, trade: UnifiedTrade) -> Optional[dict]:
        """Verarbeitet Trade und gibt abgeschlossene Candle zurück falls vorhanden"""
        key = self._candle_key(trade)
        current_time = trade.timestamp
        
        # Neue Kerze starten wenn:
        # - Erste Trade für diesen Key
        # - Oder Zeit über nächste Intervallgrenze
        if key not in self.candles:
            self.candles[key] = self._new_candle(trade)
            return None
        
        candle = self.candles[key]
        candle_start = candle["start"]
        candle_end = candle_start + timedelta(seconds=self.resolution)
        
        # Prüfe ob Trade in nächstes Intervall gehört
        if current_time >= candle_end:
            completed_candle = self._complete_candle(key)
            self.candles[key] = self._new_candle(trade)
            return completed_candle
        
        # Bestehende Kerze aktualisieren
        candle["high"] = max(candle["high"], trade.price)
        candle["low"] = min(candle["low"], trade.price)
        candle["close"] = trade.price
        candle["volume"] += trade.size
        candle["trades"] += 1
        candle["last_update"] = current_time
        
        return None

    def _round_time(self, dt: datetime) -> datetime:
        """Rundet Zeit auf die letzte Intervallgrenze"""
        timestamp = dt.timestamp()
        interval = self.resolution
        rounded_timestamp = timestamp - (timestamp % interval)
        return datetime.utcfromtimestamp(rounded_timestamp)

    def _new_candle(self, trade: UnifiedTrade) -> dict:
        """Erstellt eine neue Kerze basierend auf Trade"""
        candle_start = self._round_time(trade.timestamp)
        
        return {
            "exchange": trade.exchange,
            "symbol": trade.symbol,
            "market": trade.market.value,
            "resolution": self.resolution,
            "start": candle_start,
            "open": trade.price,
            "high": trade.price,
            "low": trade.price,
            "close": trade.price,
            "volume": trade.size,
            "trades": 1,
            "last_update": trade.timestamp
        }

    def _complete_candle(self, key: str) -> Optional[dict]:
        """Gibt abgeschlossene Kerze zurück und entfernt sie"""
        if key in self.candles:
            candle = self.candles[key].copy()
            candle["end"] = candle["start"] + timedelta(seconds=self.resolution)
            candle["ts"] = candle["start"]  # ClickHouse timestamp
            del self.candles[key]
            return candle
        return None

    def flush_all(self) -> List[dict]:
        """Gibt alle fertigen Kerzen zurück und leert Cache"""
        completed = []
        current_time = datetime.utcnow()
        
        for key in list(self.candles.keys()):
            candle = self.candles[key]
            candle_end = candle["start"] + timedelta(seconds=self.resolution)
            
            # Kerze ist fertig wenn Intervall abgeschlossen oder zu lange inaktiv
            is_complete = current_time >= candle_end
            is_stale = current_time - candle.get("last_update", candle["start"]) > self.cache_ttl
            
            if is_complete or is_stale:
                if completed_candle := self._complete_candle(key):
                    completed.append(completed_candle)
                    logger.debug(f"Flushed candle: {key} {self.resolution}s")
        
        if completed:
            logger.info(f"Flushed {len(completed)} candles for {self.resolution}s resolution")
        
        return completed

    def get_active_candles_count(self) -> int:
        """Gibt Anzahl aktiver Candles zurück (für Monitoring)"""
        return len(self.candles)

    def cleanup_stale_candles(self):
        """Entfernt zu alte inaktive Candles"""
        current_time = datetime.utcnow()
        stale_keys = []
        
        for key, candle in self.candles.items():
            last_update = candle.get("last_update", candle["start"])
            if current_time - last_update > self.cache_ttl:
                stale_keys.append(key)
        
        for key in stale_keys:
            del self.candles[key]
            logger.debug(f"Cleaned up stale candle: {key}")
        
        if stale_keys:
            logger.info(f"Cleaned up {len(stale_keys)} stale candles")
