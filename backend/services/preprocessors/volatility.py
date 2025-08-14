"""Volatility Analysis Processor"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .base import BasePreprocessor, PreprocessorResult


class VolatilityProcessor(BasePreprocessor):
    """Analyzes market volatility"""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize volatility processor"""
        super().__init__(config)
        self.name = "volatility"

    def validate_input(self, data: Any) -> bool:
        return isinstance(data, list) and len(data) > 0 and "close" in data[0]

    def process(self, data: List[Dict]) -> PreprocessorResult:
        """Process volatility data"""
        df = pd.DataFrame(data)

        return PreprocessorResult(
            processor_name=self.name,
            timestamp=datetime.now(),
            data={
                "current_volatility": self._calculate_current_volatility(df),
                "volatility_bands": self._calculate_volatility_bands(df),
                "bollinger_bands": self._calculate_bollinger_bands(df),
                "atr": self._calculate_atr(df),
                "historical_volatility": self._calculate_historical_volatility(df),
                "volatility_regime": self._determine_volatility_regime(df),
                "volatility_trend": self._analyze_volatility_trend(df),
                "volatility_events": self._detect_volatility_events(df),
                "volatility_comparison": self._compare_volatility(df),
            },
            metrics={
                "current_volatility": self._calculate_current_volatility(df),
                "average_volatility": self._calculate_average_volatility(df),
                "volatility_percentile": self._calculate_volatility_percentile(df),
                "volatility_zscore": self._calculate_volatility_zscore(df),
            },
            signals=self._generate_volatility_signals(df),
        )

    def _calculate_volatility_bands(self, df: pd.DataFrame) -> Dict:
        """Calculate Bollinger Bands"""
        if len(df) < 20:
            return {}

        sma = df["close"].rolling(20).mean()
        std = df["close"].rolling(20).std()

        return {
            "upper": sma.iloc[-1] + (2 * std.iloc[-1]),
            "middle": sma.iloc[-1],
            "lower": sma.iloc[-1] - (2 * std.iloc[-1]),
            "bandwidth": 4 * std.iloc[-1],
        }

    def _calculate_historical_volatility(self, df: pd.DataFrame) -> Dict:
        """Calculate historical volatility over different periods"""
        returns = df["close"].pct_change()

        volatilities = {}
        for period in [10, 20, 50]:
            if len(df) > period:
                vol = returns.rolling(period).std() * np.sqrt(252)  # Annualized
                volatilities[f"hv_{period}"] = vol.iloc[-1] * 100

        return volatilities

    def _calculate_current_volatility(self, df: pd.DataFrame) -> float:
        """Calculate current volatility"""
        if len(df) < 20:
            return 0

        returns = df["close"].pct_change()
        return returns.tail(20).std() * np.sqrt(252) * 100

    def _calculate_volatility_percentile(self, df: pd.DataFrame) -> float:
        """Calculate where current volatility sits historically"""
        if len(df) < 50:
            return 50

        returns = df["close"].pct_change()
        vols = returns.rolling(20).std()
        current_vol = vols.iloc[-1]

        return (vols <= current_vol).mean() * 100

    def _determine_volatility_regime(self, df: pd.DataFrame) -> str:
        """Determine current volatility regime"""
        current_vol = self._calculate_current_volatility(df)

        # Use absolute thresholds for more predictable classification
        if current_vol < 15:
            return "low"
        elif current_vol < 30:
            return "normal"
        elif current_vol < 50:
            return "high"
        else:
            return "extreme"

    def _generate_volatility_signals(self, df: pd.DataFrame) -> List[str]:
        """Generate volatility-based signals"""
        signals = []

        regime = self._determine_volatility_regime(df)

        if regime == "low":
            signals.append("Low volatility - potential breakout ahead")
        elif regime == "high":
            signals.append("High volatility - increased risk")
        elif regime == "extreme":
            signals.append("Extreme volatility detected - use caution")

        # Check for volatility events
        events = self._detect_volatility_events(df)
        if events:
            signals.append(
                f"Volatility spike detected - magnitude {events[-1]['magnitude']:.1f}"
            )

        # Check Bollinger Band squeeze
        bands = self._calculate_volatility_bands(df)
        if bands and bands["bandwidth"] < df["close"].iloc[-1] * 0.02:
            signals.append("Bollinger Band squeeze - volatility expansion expected")

        # Check volatility trend
        vol_trend = self._analyze_volatility_trend(df)
        if vol_trend["direction"] == "increasing" and vol_trend["rate_of_change"] > 20:
            signals.append("Volatility rapidly increasing")
        elif (
            vol_trend["direction"] == "decreasing" and vol_trend["rate_of_change"] < -20
        ):
            signals.append("Volatility rapidly decreasing")

        return signals

    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> Dict:
        """Calculate detailed Bollinger Bands with position"""
        if len(df) < 20:
            return {"upper": 0, "middle": 0, "lower": 0, "width": 0, "position": 0.5}

        sma = df["close"].rolling(20).mean()
        std = df["close"].rolling(20).std()
        current_price = df["close"].iloc[-1]

        upper = sma.iloc[-1] + (2 * std.iloc[-1])
        middle = sma.iloc[-1]
        lower = sma.iloc[-1] - (2 * std.iloc[-1])
        width = upper - lower

        # Calculate position within bands (0 = lower band, 1 = upper band)
        position = (current_price - lower) / width if width > 0 else 0.5

        return {
            "upper": float(upper),
            "middle": float(middle),
            "lower": float(lower),
            "width": float(width),
            "position": max(0, min(1, position)),
        }

    def _calculate_atr(self, df: pd.DataFrame) -> Dict:
        """Calculate Average True Range"""
        if len(df) < 14 or "high" not in df or "low" not in df:
            return {"current": 0, "average": 0, "percentile": 50}

        # True Range calculation
        tr1 = df["high"] - df["low"]
        tr2 = abs(df["high"] - df["close"].shift())
        tr3 = abs(df["low"] - df["close"].shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR is the moving average of TR
        atr_14 = tr.rolling(14).mean()
        current_atr = atr_14.iloc[-1]
        average_atr = atr_14.mean()

        # Calculate percentile
        percentile = (atr_14 <= current_atr).mean() * 100

        return {
            "current": float(current_atr),
            "average": float(average_atr),
            "percentile": float(percentile),
        }

    def _analyze_volatility_trend(self, df: pd.DataFrame) -> Dict:
        """Analyze volatility trend over time"""
        if len(df) < 40:
            return {"direction": "neutral", "strength": 0, "rate_of_change": 0}

        returns = df["close"].pct_change()
        vol_series = returns.rolling(10).std() * np.sqrt(252) * 100

        # Use linear regression on volatility series to detect trend
        vol_values = vol_series.dropna()
        if len(vol_values) < 20:
            return {"direction": "neutral", "strength": 0, "rate_of_change": 0}

        x = np.arange(len(vol_values))
        slope = np.polyfit(x, vol_values.values, 1)[0]

        # Calculate rate of change based on slope
        rate_of_change = (
            slope * len(vol_values) / vol_values.mean() * 100
            if vol_values.mean() > 0
            else 0
        )

        if rate_of_change > 5:
            direction = "increasing"
            strength = min(100, abs(rate_of_change))
        elif rate_of_change < -5:
            direction = "decreasing"
            strength = min(100, abs(rate_of_change))
        else:
            direction = "stable"
            strength = abs(rate_of_change)

        return {
            "direction": direction,
            "strength": float(strength),
            "rate_of_change": float(rate_of_change),
        }

    def _detect_volatility_events(self, df: pd.DataFrame) -> List[Dict]:
        """Detect volatility spikes and unusual events"""
        events = []

        if len(df) < 30:
            return events

        returns = df["close"].pct_change()
        vol_series = returns.rolling(10).std()
        vol_mean = vol_series.mean()
        vol_std = vol_series.std()

        threshold = vol_mean + (2 * vol_std)

        for i in range(len(vol_series)):
            if pd.notna(vol_series.iloc[i]) and vol_series.iloc[i] > threshold:
                events.append(
                    {
                        "type": "volatility_spike",
                        "position": i,
                        "magnitude": float((vol_series.iloc[i] - vol_mean) / vol_std),
                        "volatility": float(vol_series.iloc[i] * 100),
                    }
                )

        return events[-5:]  # Return last 5 events

    def _compare_volatility(self, df: pd.DataFrame) -> Dict:
        """Compare current volatility to historical levels"""
        if len(df) < 50:
            return {"vs_average": 1.0, "vs_median": 1.0, "vs_recent": 1.0}

        returns = df["close"].pct_change()
        current_vol = returns.tail(20).std() * np.sqrt(252) * 100

        all_vol = returns.rolling(20).std() * np.sqrt(252) * 100
        all_vol = all_vol.dropna()

        if len(all_vol) == 0:
            return {"vs_average": 1.0, "vs_median": 1.0, "vs_recent": 1.0}

        vs_average = current_vol / all_vol.mean() if all_vol.mean() > 0 else 1.0
        vs_median = current_vol / all_vol.median() if all_vol.median() > 0 else 1.0

        recent_vol = (
            all_vol.iloc[-40:-20].mean() if len(all_vol) >= 40 else all_vol.mean()
        )
        vs_recent = current_vol / recent_vol if recent_vol > 0 else 1.0

        return {
            "vs_average": float(vs_average),
            "vs_median": float(vs_median),
            "vs_recent": float(vs_recent),
        }

    def _calculate_average_volatility(self, df: pd.DataFrame) -> float:
        """Calculate average historical volatility"""
        if len(df) < 20:
            return 0

        returns = df["close"].pct_change()
        vol_series = returns.rolling(20).std() * np.sqrt(252) * 100

        return float(vol_series.mean())

    def _calculate_volatility_zscore(self, df: pd.DataFrame) -> float:
        """Calculate volatility z-score"""
        if len(df) < 30:
            return 0

        returns = df["close"].pct_change()
        vol_series = returns.rolling(20).std()

        current_vol = vol_series.iloc[-1]
        vol_mean = vol_series.mean()
        vol_std = vol_series.std()

        if vol_std > 0:
            return float((current_vol - vol_mean) / vol_std)
        return 0
