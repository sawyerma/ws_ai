# backend/indicators/six_sigma.py

import pandas as pd

def six_sigma_upper(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """
    Berechnet das obere Six-Sigma-Band für 'close'.
    Args:
        df (pd.DataFrame): DataFrame mit Spalte 'close'
        window (int): Rolling-Window-Länge (default 20)
    Returns:
        pd.Series: obere Six-Sigma-Grenze
    """
    mean = df['close'].rolling(window=window).mean()
    std = df['close'].rolling(window=window).std()
    return mean + 6 * std

def six_sigma_lower(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """
    Berechnet das untere Six-Sigma-Band für 'close'.
    Args:
        df (pd.DataFrame): DataFrame mit Spalte 'close'
        window (int): Rolling-Window-Länge (default 20)
    Returns:
        pd.Series: untere Six-Sigma-Grenze
    """
    mean = df['close'].rolling(window=window).mean()
    std = df['close'].rolling(window=window).std()
    return mean - 6 * std
