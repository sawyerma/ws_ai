import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import httpx

BASE_URL = "https://api.bitget.com"
logger = logging.getLogger("bitget-rest-utils")


async def fetch_spot_symbols() -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{BASE_URL}/api/v2/spot/public/symbols")
        r.raise_for_status()
        return r.json().get("data", [])


async def fetch_futures_symbols(product_type: str) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{BASE_URL}/api/v2/mix/market/contracts",
            params={"productType": product_type}
        )
        r.raise_for_status()
        return r.json().get("data", [])


async def fetch_spot_tickers() -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{BASE_URL}/api/spot/v1/market/tickers")
        r.raise_for_status()
        return r.json().get("data", [])


async def fetch_futures_tickers(product_type: str) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{BASE_URL}/api/mix/v1/market/tickers",
            params={"productType": product_type}
        )
        r.raise_for_status()
        return r.json().get("data", [])


async def fetch_orderbook(
    symbol: str,
    market_type: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Holt das Orderbuch für Spot oder Futures (USDT-M, Coin-M).
    - Spot: symbol_SPBL, type=step0
    - USDT-M: symbol_UMCBL, type=step0
    - Coin-M: symbol_DMCBL, type=step0
    """
    symbol_up = symbol.replace("_", "").upper()
    async with httpx.AsyncClient(timeout=10.0) as client:
        if market_type == "spot":
            url = f"{BASE_URL}/api/spot/v1/market/depth"
            params = {
                "symbol": f"{symbol_up}_SPBL",
                "type": "step0",
                "limit": limit
            }

        elif market_type == "usdtm":
            url = f"{BASE_URL}/api/mix/v1/market/depth"
            params = {
                "symbol": f"{symbol_up}_UMCBL",
                "type": "step0",
                "limit": limit
            }

        elif market_type == "coinm":
            url = f"{BASE_URL}/api/mix/v1/market/depth"
            params = {
                "symbol": f"{symbol_up}_DMCBL",
                "type": "step0",
                "limit": limit
            }

        else:
            raise ValueError(f"Unbekannter market_type: {market_type!r}")

        r = await client.get(url, params=params)
        r.raise_for_status()
        payload = r.json()
        data = payload.get("data", {})
        # data["asks"] und data["bids"] sind Listen von [price, size]
        return {"asks": data.get("asks", []), "bids": data.get("bids", [])}


async def fetch_ohlc(
    symbol: str,
    market: str = "spot",
    resolution: str = "1m",
    limit: int = 200,
    end_time: Optional[datetime] = None
) -> List[Any]:
    """
    Holt OHLC-Candles:
    - Spot über /api/v2/spot/public/candles
    - Futures (USDT-M & Coin-M) über /api/mix/v1/market/history-candles
    """
    end_ts = int((end_time or datetime.now(timezone.utc)).timestamp() * 1000)
    symbol_up = symbol.replace("_", "").upper()

    async with httpx.AsyncClient(timeout=10.0) as client:
        if market == "spot":
            url = f"{BASE_URL}/api/v2/spot/public/candles"
            params = {
                "symbol": symbol_up,
                "period": resolution,
                "endTime": end_ts,
                "limit": limit,
            }
        elif market in ("usdtm", "coinm"):
            # Für beide FUTURES verwenden wir denselben Endpoint
            url = f"{BASE_URL}/api/mix/v1/market/history-candles"
            # Bitget erwartet hier eine numerische Granularität in Sekunden
            # 1m -> 60, 1h -> 3600, 1d -> 86400, etc.
            # Wir extrahieren nur die Zahl und die Einheit:
            unit = resolution[-1]
            qty = int(resolution[:-1])
            factor = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
            granularity = qty * factor

            params = {
                "symbol": symbol_up,
                "granularity": granularity,
                "endTime": end_ts,
                "limit": limit,
            }
        else:
            raise ValueError(f"Unbekannter market: {market!r}")

        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json().get("data", [])
