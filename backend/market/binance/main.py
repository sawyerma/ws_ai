#!/usr/bin/env python3
import asyncio
import logging
import signal
import sys
from datetime import datetime
from market.binance.config import SystemConfig
from market.binance.collector import BinanceDataCollector

config = SystemConfig()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("binance_collector.log")
    ]
)
logger = logging.getLogger("binance-main")

collector = None

async def shutdown(signal, loop):
    global collector
    logger.info(f"Received exit signal {signal.name}...")
    if collector:
        await collector.stop()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    logger.info("Shutdown complete")

async def main():
    global collector
    collector = BinanceDataCollector(config)
    
    # Signal handler
    loop = asyncio.get_running_loop()
    for sig in [signal.SIGINT, signal.SIGTERM]:
        loop.add_signal_handler(
            sig, 
            lambda s=sig: asyncio.create_task(shutdown(s, loop))
        )
    
    try:
        await collector.start()
        # Warte auf Beendigungssignal
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Main task cancelled")
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
        logger.info("Application shutdown complete")
