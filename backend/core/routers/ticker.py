import logging
import traceback
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from exchanges.bitget.rest_utils import fetch_spot_tickers, fetch_futures_tickers

router = APIRouter()
logger = logging.getLogger("trading-api")


@router.get("/ticker")
async def get_ticker() -> List[Dict[str, Any]]:
    """
    Holt aktuelle Ticker/Preise für alle Symbole und Märkte von Bitget REST.
    """
    try:
        out: List[Dict[str, Any]] = []

        # Spot-Ticker
        spot_tickers = await fetch_spot_tickers()
        for tk in spot_tickers:
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
        usdtm_tickers = await fetch_futures_tickers("umcbl")
        for tk in usdtm_tickers:
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

        # Coin-Margined Futures
        coinm_tickers = await fetch_futures_tickers("dmcbl")
        for tk in coinm_tickers:
            out.append({
                "symbol":      tk["symbol"],
                "last":        float(tk.get("last", 0)),
                "high24h":     float(tk.get("high24h", 0)),
                "low24h":      float(tk.get("low24h", 0)),
                "changeRate":  float(tk.get("changeRate", 0)),
                "baseVol":     float(tk.get("baseVol", 0)),
                "quoteVol":    float(tk.get("quoteVol", 0)),
                "market_type": "coinm",
            })

        # USDC-Margined Futures
        usdcm_tickers = await fetch_futures_tickers("cmcbl")
        for tk in usdcm_tickers:
            out.append({
                "symbol":      tk["symbol"],
                "last":        float(tk.get("last", 0)),
                "high24h":     float(tk.get("high24h", 0)),
                "low24h":      float(tk.get("low24h", 0)),
                "changeRate":  float(tk.get("changeRate", 0)),
                "baseVol":     float(tk.get("baseVol", 0)),
                "quoteVol":    float(tk.get("quoteVol", 0)),
                "market_type": "usdcm",
            })

        return out

    except Exception as e:
        logger.error(f"TICKER-API-ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ticker-API-Fehler: {e}")
