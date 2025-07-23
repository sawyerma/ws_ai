import logging
import time

logger = logging.getLogger("circuit-breaker")

class CircuitBreaker:
    def __init__(self, threshold: int = 5, reset_timeout: int = 60):
        self.threshold = threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.tripped = False
        self.last_failure_time = None

    def trip(self) -> bool:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if not self.tripped and self.failure_count >= self.threshold:
            self.tripped = True
            logger.critical("Circuit breaker tripped! Blocking further requests.")
            return True
        return False

    def reset(self):
        self.failure_count = 0
        self.tripped = False
        logger.info("Circuit breaker reset")
    
    def should_allow(self) -> bool:
        if self.tripped:
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.reset()
                return True
            return False
        return True
