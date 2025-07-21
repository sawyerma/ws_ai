import logging
import traceback
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from market.bitget.services.bitget_rest import BitgetRestAPI
from db.clickhouse import fetch_symbols
from core.services.cache_service import cached, SYMBOLS_TTL, TICKER_TTL

router = APIRouter()
logger = logging.getLogger("trading-api")


@router.get("/symbols")
@cached("symbols", ttl=SYMBOLS_TTL)  # Cache für 5 Minuten
async def get_symbols():
    """
    Holt alle verfügbaren Symbole von Bitget REST und aus der lokalen Datenbank für Dropdowns etc.
    Mit Redis-Cache für minimale Latenz.
    """
    try:
        api = BitgetRestAPI()
        
        spot_symbols_data = await api.fetch_spot_symbols()
        spot_symbols = spot_symbols_data.get("data", []) if spot_symbols_data.get("code") == "00000" else []
        
        usdtm_symbols_data = await api.fetch_futures_symbols("USDT-FUTURES")
        usdtm_symbols = usdtm_symbols_data.get("data", []) if usdtm_symbols_data.get("code") == "00000" else []
        
        coinm_symbols_data = await api.fetch_futures_symbols("COIN-FUTURES")
        coinm_symbols = coinm_symbols_data.get("data", []) if coinm_symbols_data.get("code") == "00000" else []
        
        usdcm_symbols_data = await api.fetch_futures_symbols("USDC-FUTURES")
        usdcm_symbols = usdcm_symbols_data.get("data", []) if usdcm_symbols_data.get("code") == "00000" else []
        
        all_api = spot_symbols + usdtm_symbols + coinm_symbols + usdcm_symbols

        db_symbols = fetch_symbols()
        await api.close()
        
        return {
            "symbols": all_api,
            "db_symbols": db_symbols
        }
    except Exception as e:
        logger.error(f"SYMBOLS-API-ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Bitget-API-Fehler: {e}")


@router.get("/ticker")
@cached("ticker:all", ttl=TICKER_TTL)  # Cache für 10 Sekunden
async def get_ticker():
    """
    Holt aktuelle Ticker/Preise für alle Symbole und Märkte von Bitget REST.
    Mit Redis-Cache für minimale Latenz.
    """
    try:
        api = BitgetRestAPI()
        out: List[Dict[str, Any]] = []

        # Spot-Ticker
        spot_tickers_data = await api.fetch_spot_tickers()
        if spot_tickers_data.get("code") == "00000":
            for tk in spot_tickers_data.get("data", []):
                out.append({
                    "symbol":      tk["symbol"],
                    "last":        float(tk.get("last", 0)),
                    "high24h":     float(tk.get("high24h", 0)),
                    "low24h":      float(tk.get("low24h", 0)),
                    "changeRate":  float(tk.get("changeRate", 0)),
                    "baseVol":     float(tk.get("baseVol", 0)),
                    "quoteVol":    float(tk.get("quoteVol", 0)),
                    "market_type": "spot",
                })

        # USDT-Margined Futures  
        usdtm_tickers_data = await api.fetch_futures_tickers("USDT-FUTURES")
        if usdtm_tickers_data.get("code") == "00000":
            for tk in usdtm_tickers_data.get("data", []):
                out.append({
                    "symbol":      tk["symbol"],
                    "last":        float(tk.get("last", 0)),
                    "high24h":     float(tk.get("high24h", 0)),
                    "low24h":      float(tk.get("low24h", 0)),
                    "changeRate":  float(tk.get("changeRate", 0)),
                    "baseVol":     float(tk.get("baseVol", 0)),
                    "quoteVol":    float(tk.get("quoteVol", 0)),
                    "market_type": "usdtm",
                })

        await api.close()
        return out

    except Exception as e:
        logger.error(f"TICKER-API-ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ticker-API-Fehler: {e}")
