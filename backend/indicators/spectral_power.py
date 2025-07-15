# backend/indicators/spectral_power.py

import pandas as pd
import numpy as np

def spectral_power(df: pd.DataFrame, window: int = 128) -> pd.Series:
    """
    Berechnet die mittlere Spektralpower (FFT) für das 'close'-Signal.
    Args:
        df (pd.DataFrame): DataFrame mit Spalte 'close'
        window (int): Fensterlänge für die FFT (default 128)
    Returns:
        pd.Series: Spektralpower je Bar (NaN für die ersten 'window' Werte)
    """
    power = [np.nan] * window
    closes = df['close'].values
    for i in range(window, len(closes)):
        segment = closes[i-window:i]
        spectrum = np.fft.fft(segment)
        segment_power = np.abs(spectrum[1:window//2]).mean()
        power.append(segment_power)
    return pd.Series(power, index=df.index)

