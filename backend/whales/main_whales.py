import asyncio
import logging
import signal
from whales.collector_manager_whales import collector_manager
from whales.services.price_service_whales import price_service

logger = logging.getLogger(__name__)

def handle_shutdown(signum, frame):
    logger.info("🛑 Received shutdown signal for Whale system...")
    asyncio.create_task(graceful_shutdown())

async def graceful_shutdown():
    logger.info("Stopping all whale collectors...")
    await collector_manager.stop_all()
    logger.info("✅ All whale collectors stopped.")

async def start_whale_system():
    """Start the Whale Monitoring System"""
    logger.info("🐋 Starting Whale Monitoring System")
    
    # Preisservice starten
    await price_service.start()
    logger.info("✅ Whale Price Service started")
    
    # Collector starten
    await collector_manager.init_from_config()
    logger.info("✅ Whale Collectors started")
    
    logger.info("🚀 Whale Monitoring System is fully operational")

async def stop_whale_system():
    """Stop the Whale Monitoring System"""
    logger.info("🛑 Stopping Whale Monitoring System")
    await collector_manager.stop_all()
    logger.info("✅ Whale Monitoring System stopped")

if __name__ == "__main__":
    # Standalone-Modus für Whale-System
    try:
        # Shutdown-Handler registrieren
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        
        asyncio.run(start_whale_system())
        
        # Halte System am Leben
        asyncio.run(asyncio.Future())
        
    except KeyboardInterrupt:
        logger.info("🛑 Whale system interrupted by user")
    except Exception as e:
        logger.critical(f"Critical whale system failure: {e}")
