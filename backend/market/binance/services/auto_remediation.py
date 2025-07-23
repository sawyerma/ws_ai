import asyncio
import logging
from market.binance.utils.circuit_breaker import CircuitBreaker

logger = logging.getLogger("auto-remediation")

class AutoRemediationSystem:
    def __init__(self):
        self.circuit_breakers = {}
        self.running = True
        self.monitor_task = None

    async def start(self):
        self.monitor_task = asyncio.create_task(self.monitor_system())
        logger.info("Auto-remediation system started")

    async def monitor_system(self):
        while self.running:
            await self.check_system_health()
            await asyncio.sleep(30)
    
    async def check_system_health(self):
        for component, breaker in self.circuit_breakers.items():
            if breaker.tripped:
                logger.warning(f"Component {component} is tripped! Initiating remediation...")
                await self.remediate(component)

    def register_component(self, component_name: str, threshold: int = 5):
        self.circuit_breakers[component_name] = CircuitBreaker(threshold)
        logger.info(f"Registered circuit breaker for {component_name}")

    async def handle_failure(self, component_name: str, error: Exception):
        if component_name in self.circuit_breakers:
            breaker = self.circuit_breakers[component_name]
            if breaker.trip():
                logger.error(f"Critical failure in {component_name}: {error}")
                await self.remediate(component_name)

    async def remediate(self, component_name: str):
        logger.warning(f"Attempting auto-remediation for {component_name}")
        try:
            # Beispiel: Neustart der Komponente
            if "websocket" in component_name:
                logger.info(f"Restarting WebSocket for {component_name}")
                await asyncio.sleep(3)
            elif "database" in component_name:
                logger.info(f"Reconnecting to database for {component_name}")
                await asyncio.sleep(2)
            else:
                logger.info(f"Generic remediation for {component_name}")
                await asyncio.sleep(1)
            
            self.circuit_breakers[component_name].reset()
            logger.info(f"Remediation successful for {component_name}")
        except Exception as e:
            logger.critical(f"Remediation failed: {e}")

    async def stop(self):
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Auto-remediation system stopped")
