# backend/indicators/pipeline.py

import pandas as pd

# Einzelne Indikatoren importieren (immer als eigene Datei, sauber getrennt!)
from .alma import alma
from .spectral_power import spectral_power
from .six_sigma import six_sigma_upper, six_sigma_lower
from .whale_impact import whale_impact
from .elliott_wave import elliott_wave

def compute_indicators(
    df: pd.DataFrame,
    indicators: list,
    whale_events: pd.DataFrame = None
) -> pd.DataFrame:
    """
    Kombiniert beliebig viele Indikatoren, dynamisch nach Auswahl.
    Args:
        df (pd.DataFrame): OHLCV DataFrame
        indicators (list): z. B. ["alma", "six_sigma_upper", "spectral_power", "whale_impact"]
        whale_events (pd.DataFrame): Nur wenn whale_impact berechnet werden soll
    Returns:
        pd.DataFrame: mit allen gewünschten Indikator-Spalten
    """
    df = df.copy()
    if "alma" in indicators:
        df["alma"] = alma(df)
    if "spectral_power" in indicators:
        df["spectral_power"] = spectral_power(df)
    if "six_sigma_upper" in indicators:
        df["six_sigma_upper"] = six_sigma_upper(df)
    if "six_sigma_lower" in indicators:
        df["six_sigma_lower"] = six_sigma_lower(df)
    if "whale_impact" in indicators and whale_events is not None:
        df["whale_impact"] = whale_impact(df, whale_events)
    if "elliott_wave" in indicators:
        df["elliott_wave"] = elliott_wave(df)
    # Hier beliebig viele weitere Indikatoren einbinden!
    return df
