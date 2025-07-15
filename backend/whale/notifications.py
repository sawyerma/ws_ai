# /backend/whale/notifications.py

import httpx
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def notify_webhooks(hooks, payload):
    """
    Sendet Payload an alle Webhooks in hooks-Liste (async).
    """
    async with httpx.AsyncClient() as client:
        for url in hooks:
            try:
                resp = await client.post(url, json=payload, timeout=5)
                logger.info(f"[NOTIFY] Webhook {url}: {resp.status_code}")
            except Exception as e:
                logger.error(f"[NOTIFY ERROR] {url}: {e}")
