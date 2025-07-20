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
