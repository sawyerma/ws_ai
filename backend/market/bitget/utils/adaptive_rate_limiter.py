import asyncio
import time
import logging

logger = logging.getLogger("rate-limiter")

class AdaptiveRateLimiter:
    """Intelligent rate limiting with API response time learning"""
    
    def __init__(self, base_rps: float, name: str = "default"):
        self.base_rps = base_rps
        self.current_rps = base_rps
        self.name = name
        self.response_times = []
        self.error_count = 0
        self.success_count = 0
        self.min_rps = base_rps * 0.3
        self.max_rps = base_rps * 2.0
        self.fast_threshold = 0.3
        self.slow_threshold = 1.5
        self.error_penalty = 0.7
        self.success_bonus = 1.05
        self._last_request = 0
        self._consecutive_errors = 0
        self._consecutive_successes = 0
        
    async def acquire(self) -> None:
        current_time = time.time()
        min_interval = 1.0 / self.current_rps
        elapsed = current_time - self._last_request
        
        if elapsed < min_interval:
            delay = min_interval - elapsed
            await asyncio.sleep(delay)
            
        self._last_request = time.time()
        
    def record_success(self, response_time: float) -> None:
        self.response_times.append(response_time)
        self.success_count += 1
        self._consecutive_successes += 1
        self._consecutive_errors = 0
        self._adjust_rate_on_success(response_time)
        
    def record_error(self, error_type: str = "unknown") -> None:
        self.error_count += 1
        self._consecutive_errors += 1
        self._consecutive_successes = 0
        
        if self._consecutive_errors == 1:
            self.current_rps = max(self.current_rps * 0.8, self.min_rps)
        elif self._consecutive_errors <= 3:
            self.current_rps = max(self.current_rps * 0.6, self.min_rps)
        else:
            self.current_rps = self.min_rps
            
    def _adjust_rate_on_success(self, response_time: float) -> None:
        if len(self.response_times) < 5:
            return
            
        recent_times = self.response_times[-10:]
        avg_response_time = sum(recent_times) / len(recent_times)
        
        old_rps = self.current_rps
        
        if avg_response_time < self.fast_threshold and self._consecutive_errors == 0:
            if self._consecutive_successes >= 5:
                self.current_rps = min(self.current_rps * self.success_bonus, self.max_rps)
        elif avg_response_time > self.slow_threshold:
            self.current_rps = max(self.current_rps * 0.9, self.min_rps)
            
    def get_stats(self) -> dict:
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        total_requests = self.success_count + self.error_count
        error_rate = (self.error_count / total_requests) * 100 if total_requests > 0 else 0
        
        return {
            "name": self.name,
            "current_rps": self.current_rps,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time
        }
