import logging
from fastapi import APIRouter, HTTPException, Query
from market.bitget.services.bitget_rest import BitgetRestAPI
from core.services.cache_service import cached

router = APIRouter()
logger = logging.getLogger("trading-api")

@router.get("/orderbook")
@cached("orderbook", ttl=2)  # Cache für 2 Sekunden (sehr kurz für Orderbook)
async def get_orderbook(
    symbol: str = Query("BTCUSDT"),  # Default-Symbol
    market_type: str = Query("spot"),
    limit: int = Query(10)
):
    """
    Holt Orderbuch für ein Symbol/Markt über zentrale Bitget-Utility.
    """
    try:
        api = BitgetRestAPI()
        
        if market_type == "spot":
            response = await api.fetch_spot_orderbook(symbol, limit)
        else:
            response = await api.fetch_futures_orderbook(symbol, market_type.upper() + "-FUTURES", limit)
        
        await api.close()
        
        if response.get("code") == "00000":
            data = response.get("data", {})
            asks = [{"price": float(p), "size": float(s)} for p, s in data.get("asks", [])]
            bids = [{"price": float(p), "size": float(s)} for p, s in data.get("bids", [])]
            return {"asks": asks, "bids": bids}
        else:
            raise Exception(f"Bitget API error: {response.get('msg', 'Unknown error')}")
            
    except Exception as e:
        logger.error("Orderbook-Fehler:", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Orderbook-Error: {e}")
