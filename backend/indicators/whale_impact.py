# backend/indicators/whale_impact.py

import pandas as pd

def whale_impact(df: pd.DataFrame, whale_events: pd.DataFrame) -> pd.Series:
    """
    Whale Impact: Summiert Whale-Event-Impacts pro Candle.
    Args:
        df (pd.DataFrame): Candle-DF mit 'time' (DateTime)
        whale_events (pd.DataFrame): Events mit 'timestamp', 'impact'
    Returns:
        pd.Series: Impact per Row (float)
    """
    impacts = []
    df = df.copy()
    # Zeitzone/Format sicherstellen
    df['time'] = pd.to_datetime(df['time'])
    whale_events['timestamp'] = pd.to_datetime(whale_events['timestamp'])

    for t in df['time']:
        # Events im aktuellen Candle (z.B. 1m-Fenster)
        mask = (whale_events['timestamp'] >= t) & (whale_events['timestamp'] < t + pd.Timedelta(minutes=1))
        impacts.append(whale_events.loc[mask, 'impact'].sum())
    return pd.Series(impacts, index=df.index)
