import os
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

# Router-Importe gemäß Sawyer-Struktur!
from core.routers.trades import router as trades_router
from core.routers.symbols import router as symbols_router
from core.routers.settings import router as settings_router
from core.routers.ohlc import router as ohlc_router
from core.routers.orderbook import router as orderbook_router
from core.routers.health import router as health_router
from core.routers.ticker import router as ticker_router
from core.routers.trading import router as trading_router

from db.clickhouse import fetch_trades, fetch_bars, fetch_coin_settings, ping

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("trading-api")

# Umgebungsvariablen laden
load_dotenv()

# FastAPI-App erzeugen
app = FastAPI(title="Trading API")

# CORS aktivieren (alle Domains, Methoden, Header erlaubt)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# StaticFiles-Mount entfällt, da Frontend im eigenen Container läuft!

# Alle Router einbinden
app.include_router(trades_router)
app.include_router(symbols_router)
app.include_router(settings_router)
app.include_router(ohlc_router)
app.include_router(orderbook_router)
app.include_router(health_router)
app.include_router(ticker_router)
app.include_router(trading_router)


# Root-Redirect auf externes Frontend (optional, oder entferne die Funktion!)
@app.get("/", include_in_schema=False)
def root():
    # Falls du willst, leite auf das "richtige" Frontend weiter (kann auch entfernt werden!)
    # return RedirectResponse(url="/static/index.html")   # nur wenn StaticFiles genutzt werden!
    return {"message": "API läuft. Frontend unter http://localhost:8180"}

# Startup-Event
@app.on_event("startup")
async def on_startup():
    logger.info("Trading API gestartet & bereit!")
