import logging
import traceback
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from market.bitget.services.bitget_rest import BitgetRestAPI

router = APIRouter()
logger = logging.getLogger("trading-api")


@router.get("/ticker")
async def get_ticker() -> List[Dict[str, Any]]:
    """
    Holt aktuelle Ticker/Preise für alle Symbole und Märkte von Bitget REST.
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
