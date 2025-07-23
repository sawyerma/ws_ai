# backend/models/trade.py
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class MarketType(str, Enum):
    spot = "spot"
    usdtm = "usdtm"    # USDT-Margined Futures
    coinm = "coinm"    # Coin-Margined Futures
    usdcm = "usdcm"    # USDC-Margined Futures

class UnifiedTrade(BaseModel):
    exchange: str          # 'binance' oder 'bitget'
    symbol: str            # Handelsymbol (z.B. 'BTCUSDT')
    market: MarketType     # Markttyp aus MarketType Enum
    price: float           # Handelspreis
    size: float            # Handelsgröße/Volumen
    side: str              # 'buy' oder 'sell'
    timestamp: datetime    # Zeitstempel des Handels
    exchange_id: str       # Original-ID des Trades (Exchange-spezifisch)
