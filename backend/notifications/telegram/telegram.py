# /backend/notifications/telegram/telegram.py

import httpx
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# === TELEGRAM KONFIGURATION ===
# Einmal mit @BotFather einen Bot erstellen, Token kopieren:
TELEGRAM_BOT_TOKEN = "DEIN-TELEGRAM-BOT-TOKEN"
# Chat-ID: Kann ein User, Gruppe oder Kanal sein. Zum Testen zuerst an eigenen User schicken.
TELEGRAM_CHAT_ID = "DEINE_CHAT_ID"

# --- TEXT SENDEN ---
async def send_telegram_message(text: str, chat_id: Optional[str] = None):
    """
    Sende einen Text an Telegram.
    """
    chat = chat_id or TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat, "text": text, "parse_mode": "Markdown"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            logger.info(f"[TELEGRAM] sendMessage: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"[TELEGRAM ERROR] {e}")

# --- BILD SENDEN ---
async def send_telegram_photo(image_path: str, caption: Optional[str] = None, chat_id: Optional[str] = None):
    """
    Sende ein Bild (z. B. Chart, Screenshot) an Telegram.
    """
    chat = chat_id or TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(image_path, "rb") as img:
            files = {"photo": img}
            data = {"chat_id": chat}
            if caption:
                data["caption"] = caption
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, data=data, files=files)
                logger.info(f"[TELEGRAM] sendPhoto: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"[TELEGRAM ERROR] {e}")

# --- DATEI SENDEN (z.B. CSV, PDF) ---
async def send_telegram_document(file_path: str, caption: Optional[str] = None, chat_id: Optional[str] = None):
    """
    Sende eine Datei an Telegram.
    """
    chat = chat_id or TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"chat_id": chat}
            if caption:
                data["caption"] = caption
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, data=data, files=files)
                logger.info(f"[TELEGRAM] sendDocument: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"[TELEGRAM ERROR] {e}")

# --- UNIVERSAL BUILDER ---
async def post_anything(text: Optional[str] = None, image: Optional[str] = None, file: Optional[str] = None):
    """
    Sende beliebige Info (Text, Bild, Datei) an Telegram.
    """
    if text:
        await send_telegram_message(text)
    if image:
        await send_telegram_photo(image)
    if file:
        await send_telegram_document(file)
