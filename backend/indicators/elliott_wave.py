import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import concurrent.futures
from functools import lru_cache
import time
import json
import hashlib
from scipy.signal import argrelextrema

# -------------------------------------------
# 1. Universelle Datenstrukturen
# -------------------------------------------
class WaveType(Enum):
    IMPULSE = "impulse"
    CORRECTION = "correction"
    DIAGONAL = "diagonal"
    TRIANGLE = "triangle"
    FLAT = "flat"
    ZIGZAG = "zigzag"
    COMPLEX = "complex"

class WaveConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SPECULATIVE = "speculative"

@dataclass
class WavePattern:
    type: WaveType
    start_idx: int
    end_idx: int
    pivot_indices: List[int]
    pivot_prices: List[float]
    score: float
    violations: List[str]
    fibonacci_levels: Dict[str, float]
    is_inverted: bool = False
    confidence: str = WaveConfidence.MEDIUM.value
    alternation_score: float = 0.0
    time_fibonacci_score: float = 0.0

# -------------------------------------------
# 2. Kernfunktionalität (hardwareunabhängig)
# -------------------------------------------
def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Berechnet den Average True Range"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr = np.maximum(high - low, 
                   np.maximum(np.abs(high - close.shift()), 
                              np.abs(low - close.shift())))
    return tr.rolling(period).mean()

def find_swing_points(df: pd.DataFrame, min_depth: int = 3, max_depth: int = 20,
                     atr_period: int = 14, volatility_factor: float = 2.0) -> pd.DataFrame:
    """Findet Swing-Punkte mit adaptiver Tiefe"""
    n = len(df)
    if n < min_depth * 2:
        return pd.DataFrame()
    
    # ATR berechnen
    atr = calculate_atr(df, atr_period)
    
    # Adaptive Tiefen berechnen
    depths = np.zeros(n, dtype=int)
    for i in range(n):
        if i < atr_period:
            depths[i] = min_depth
        else:
            volatility_ratio = atr.iloc[i] / df['close'].iloc[i] if df['close'].iloc[i] > 0 else 0
            depth = int(min_depth + (volatility_ratio * volatility_factor * (max_depth - min_depth)))
            depths[i] = np.clip(depth, min_depth, max_depth)
    
    # Swing-Punkte identifizieren
    highs = []
    lows = []
    
    for i in range(n):
        depth = depths[i]
        start_idx = max(0, i - depth)
        end_idx = min(n, i + depth + 1)
        
        # Hochpunkt
        if i > 0 and i < n - 1:
            window_high = df['high'].iloc[start_idx:end_idx]
            if (df['high'].iloc[i] == window_high.max() and 
                df['high'].iloc[i] > df['high'].iloc[i-1] and 
                df['high'].iloc[i] > df['high'].iloc[i+1]):
                highs.append(i)
        
            # Tiefpunkt
            window_low = df['low'].iloc[start_idx:end_idx]
            if (df['low'].iloc[i] == window_low.min() and 
                df['low'].iloc[i] < df['low'].iloc[i-1] and 
                df['low'].iloc[i] < df['low'].iloc[i+1]):
                lows.append(i)
    
    # Pivot-Daten erstellen
    pivot_data = []
    for idx in highs:
        pivot_data.append({
            'idx': idx,
            'price': df['high'].iloc[idx],
            'type': 'high'
        })
    
    for idx in lows:
        pivot_data.append({
            'idx': idx,
            'price': df['low'].iloc[idx],
            'type': 'low'
        })
    
    if not pivot_data:
        return pd.DataFrame()
    
    pivots = pd.DataFrame(pivot_data).sort_values('idx')
    return remove_consecutive_pivots(pivots)

def remove_consecutive_pivots(pivots: pd.DataFrame) -> pd.DataFrame:
    """Entfernt aufeinanderfolgende Pivots desselben Typs"""
    if len(pivots) <= 1:
        return pivots
    
    pivots = pivots.copy()
    pivots['group'] = (pivots['type'] != pivots['type'].shift()).cumsum()
    
    def get_extreme(group):
        if group.iloc[0]['type'] == 'high':
            return group.loc[group['price'].idxmax()]
        else:
            return group.loc[group['price'].idxmin()]
    
    result = pivots.groupby('group').apply(get_extreme)
    return result.drop('group', axis=1).reset_index(drop=True)

# -------------------------------------------
# 3. Pattern-Erkennung mit Caching
# -------------------------------------------
class PatternCache:
    """Cache für Pattern-Ergebnisse"""
    
    def __init__(self, max_size=1000):
        self.cache = {}
        self.max_size = max_size
    
    def get(self, key):
        return self.cache.get(key)
    
    def put(self, key, value):
        if len(self.cache) >= self.max_size:
            # Entferne einen zufälligen Eintrag
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = value
    
    def create_key(self, pivots, settings):
        """Erstellt einen eindeutigen Cache-Schlüssel"""
        pivots_hash = hashlib.md5(pd.util.hash_pandas_object(pivots).values.tobytes()).hexdigest()
        settings_hash = hashlib.md5(json.dumps(settings, sort_keys=True).encode()).hexdigest()
        return f"{pivots_hash}_{settings_hash}"

# -------------------------------------------
# 4. Elliott-Wellen Validierung
# -------------------------------------------
def validate_impulse_wave(prices: List[float]) -> Tuple[float, List[str]]:
    """Validiert ein Impuls-Wellenmuster"""
    if len(prices) < 5:
        return 0.0, ["Impulse wave requires at least 5 points"]
    
    violations = []
    score = 1.0
    is_bullish = prices[-1] > prices[0]
    
    # Grundregeln
    if is_bullish:
        if prices[1] <= prices[0]:
            violations.append("Wave 2 exceeds start of Wave 1")
            score -= 0.3
        if prices[3] <= prices[1]:
            violations.append("Wave 4 enters Wave 1 territory")
            score -= 0.3
    else:
        if prices[1] >= prices[0]:
            violations.append("Wave 2 exceeds start of Wave 1")
            score -= 0.3
        if prices[3] >= prices[1]:
            violations.append("Wave 4 enters Wave 1 territory")
            score -= 0.3
    
    # Wellenlängen
    waves = [
        abs(prices[1] - prices[0]),
        abs(prices[2] - prices[1]),
        abs(prices[3] - prices[2]),
        abs(prices[4] - prices[3])
    ]
    
    # Wave 3 sollte nicht die kürzeste sein
    if waves[2] < waves[0] and waves[2] < waves[3]:
        violations.append("Wave 3 is the shortest wave")
        score -= 0.4
    
    return max(0.0, score), violations

def calculate_fibonacci_levels(start: float, end: float) -> Dict[str, float]:
    """Berechnet Fibonacci-Levels"""
    diff = end - start
    return {
        "0.0": start,
        "0.236": start + 0.236 * diff,
        "0.382": start + 0.382 * diff,
        "0.5": start + 0.5 * diff,
        "0.618": start + 0.618 * diff,
        "1.0": end,
        "1.618": start + 1.618 * diff
    }

# -------------------------------------------
# 5. Hauptanalysefunktion
# -------------------------------------------
def analyze_elliott_waves(df: pd.DataFrame, 
                         min_depth: int = 3,
                         max_depth: int = 20,
                         atr_period: int = 14,
                         min_score: float = 0.6) -> Dict[str, Any]:
    """
    Universeller Elliott-Wellen-Analysator
    
    Args:
        df: DataFrame mit OHLC-Daten
        min_depth: Minimale Wellentiefe
        max_depth: Maximale Wellentiefe
        atr_period: Periode für ATR-Berechnung
        min_score: Minimaler Score für gültige Pattern
    
    Returns:
        Analyseergebnis mit Pivots und Patterns
    """
    # 1. Swing-Punkte finden
    pivots = find_swing_points(df, min_depth, max_depth, atr_period)
    
    if len(pivots) < 3:
        return {"pivots": [], "patterns": [], "error": "Insufficient pivots"}
    
    # 2. Pattern-Erkennung
    patterns = []
    pattern_defs = {
        "impulse": {"min_points": 5, "validator": validate_impulse_wave}
    }
    
    for pattern_name, defn in pattern_defs.items():
        min_points = defn["min_points"]
        validator = defn["validator"]
        
        for i in range(len(pivots) - min_points + 1):
            window = pivots.iloc[i:i+min_points]
            prices = window['price'].tolist()
            
            score, violations = validator(prices)
            if score >= min_score:
                pattern = WavePattern(
                    type=WaveType(pattern_name),
                    start_idx=int(window.iloc[0]['idx']),
                    end_idx=int(window.iloc[-1]['idx']),
                    pivot_indices=window['idx'].tolist(),
                    pivot_prices=prices,
                    score=score,
                    violations=violations,
                    fibonacci_levels=calculate_fibonacci_levels(prices[0], prices[-1]),
                    is_inverted=prices[-1] < prices[0],
                    confidence="high" if score > 0.8 else "medium"
                )
                patterns.append(asdict(pattern))
    
    # 3. Ergebnis zusammenstellen
    return {
        "pivots": pivots.to_dict(orient="records"),
        "patterns": patterns,
        "settings": {
            "min_depth": min_depth,
            "max_depth": max_depth,
            "atr_period": atr_period,
            "min_score": min_score
        }
    }

# -------------------------------------------
# 6. API für Backend-Integration
# -------------------------------------------
class ElliottWaveAnalyzer:
    """Backend-Service für Elliott-Wellen-Analyse"""
    
    def __init__(self):
        self.cache = PatternCache()
        self.performance_stats = {
            "last_analysis_time": 0,
            "average_time": 0,
            "analysis_count": 0
        }
    
    def analyze(self, data: Dict, settings: Dict = None) -> Dict:
        """Analysiert OHLC-Daten"""
        if settings is None:
            settings = {}
        
        # Konvertiere Daten zu DataFrame
        df = pd.DataFrame(data)
        
        # Cache-Schlüssel erstellen
        cache_key = self.cache.create_key(df, settings)
        
        # Cache prüfen
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Analyse durchführen
        start_time = time.time()
        result = analyze_elliott_waves(df, **settings)
        elapsed = time.time() - start_time
        
        # Performance-Tracking
        self.performance_stats["last_analysis_time"] = elapsed
        self.performance_stats["analysis_count"] += 1
        self.performance_stats["average_time"] = (
            self.performance_stats["average_time"] * (self.performance_stats["analysis_count"] - 1) + elapsed
        ) / self.performance_stats["analysis_count"]
        
        # Ergebnis cachen
        result["performance"] = {
            "analysis_time": elapsed,
            "cached": False
        }
        self.cache.put(cache_key, result)
        
        return result
    
    def get_performance(self) -> Dict:
        """Gibt Performance-Statistiken zurück"""
        return self.performance_stats

# -------------------------------------------
# 7. Beispiel für die Nutzung im Backend
# -------------------------------------------
if __name__ == "__main__":
    # Simulierte Daten (kann durch echte API-Daten ersetzt werden)
    data = {
        'open': [100, 101, 102, 101, 103, 104, 103, 105],
        'high': [102, 103, 104, 103, 105, 106, 105, 107],
        'low': [99, 100, 101, 100, 102, 103, 102, 104],
        'close': [101, 102, 103, 102, 104, 105, 104, 106],
    }
    
    # Backend-Service initialisieren
    analyzer = ElliottWaveAnalyzer()
    
    # Analyse durchführen
    result = analyzer.analyze(data)
    
    # Ergebnisse anzeigen
    print("Elliott Wave Analysis Results:")
    print(f"Found {len(result['patterns'])} patterns")
    
    for pattern in result['patterns']:
        print(f"\n{pattern['type']} pattern (Score: {pattern['score']:.2f})")
        print(f"Start: {pattern['start_idx']}, End: {pattern['end_idx']}")
        print(f"Prices: {pattern['pivot_prices']}")
        print(f"Fibonacci Levels: {pattern['fibonacci_levels']}")
    
    # Performance anzeigen
    perf = analyzer.get_performance()
    print(f"\nPerformance: Last analysis took {perf['last_analysis_time']:.4f}s")
    print(f"Average time: {perf['average_time']:.4f}s over {perf['analysis_count']} analyses")