# backend/indicators/alma.py

import pandas as pd
import pandas_ta as ta  # Voraussetzung: pip install pandas_ta

def alma(df: pd.DataFrame, window=10, sigma=6, offset=0.85) -> pd.Series:
    """
    Arnaud Legoux Moving Average (ALMA)
    Args:
        df (pd.DataFrame): OHLCV DataFrame mit Spalte 'close'
        window (int): ALMA-Länge (default 10)
        sigma (int): ALMA-Sigma (default 6)
        offset (float): ALMA-Offset (default 0.85)
    Returns:
        pd.Series: ALMA-Werte, indexiert wie df
    """
    return ta.alma(df['close'], length=window, sigma=sigma, offset=offset)
