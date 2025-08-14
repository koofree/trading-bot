"""Trend Analysis Processor"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .base import BasePreprocessor, PreprocessorResult


class TrendProcessor(BasePreprocessor):
    """Analyzes market trends using various methods"""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize trend processor"""
        super().__init__(config)
        self.name = "trend"

    def validate_input(self, data: Any) -> bool:
        return isinstance(data, list) and len(data) > 0 and "close" in data[0]

    def process(self, data: List[Dict]) -> PreprocessorResult:
        """Process trend data"""
        df = pd.DataFrame(data)

        # Calculate all trend components
        trend_direction = self._calculate_trend(df)
        moving_averages = self._calculate_moving_averages(df)
        trend_strength = self._calculate_trend_strength(df)
        linear_regression = self._calculate_linear_regression(df)
        trend_changes = self._detect_trend_changes(df)
        ma_crossovers = self._detect_ma_crossovers(df)
        trend_channel = self._calculate_trend_channel(df)
        higher_timeframe = self._analyze_higher_timeframe_trend(df)

        return PreprocessorResult(
            processor_name=self.name,
            timestamp=datetime.now(),
            data={
                "trend": trend_direction,
                "trend_direction": trend_direction,
                "moving_averages": moving_averages,
                "trend_strength": trend_strength,
                "linear_regression": linear_regression,
                "trend_changes": trend_changes,
                "ma_crossovers": ma_crossovers,
                "trend_channel": trend_channel,
                "higher_timeframe": higher_timeframe,
            },
            metrics={
                "trend_score": self._calculate_trend_score(df),
                "trend_consistency": self._calculate_trend_consistency(df),
                "trend_momentum": self._calculate_trend_momentum(df),
            },
            signals=self._generate_trend_signals(df),
        )

    def _calculate_trend(self, df: pd.DataFrame) -> str:
        """Calculate overall trend direction"""
        if len(df) < 20:
            return "insufficient_data"

        # Simple linear regression with R-squared check for trend strength
        x = np.arange(len(df))
        y = df["close"].values
        z = np.polyfit(x, y, 1)
        slope = z[0]

        # Calculate R-squared to measure trend quality
        p = np.poly1d(z)
        y_pred = p(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Calculate price range and volatility to determine threshold
        price_range = df["close"].max() - df["close"].min()
        returns = df["close"].pct_change()
        volatility = returns.std() * 100  # Percentage volatility

        # Higher volatility requires stronger trend to be classified
        base_threshold = price_range / len(df) * 0.1
        volatility_adjustment = volatility * 0.02  # Scale volatility impact
        threshold = base_threshold * (1 + volatility_adjustment)

        # Require minimum R-squared for trend classification (trend must explain data well)
        min_r_squared = 0.5  # At least 50% of variance explained for volatile data

        if r_squared < min_r_squared:
            return "sideways"  # Weak trend fit = sideways
        elif slope > threshold:
            return "uptrend"
        elif slope < -threshold:
            return "downtrend"
        else:
            return "sideways"

    def _calculate_moving_averages(self, df: pd.DataFrame) -> Dict:
        """Calculate various moving averages"""
        mas = {}

        # Simple Moving Averages
        for period in [10, 20, 50, 200]:
            if len(df) >= period:
                mas[f"ma_{period}"] = df["close"].rolling(period).mean().iloc[-1]
                mas[f"sma_{period}"] = df["close"].rolling(period).mean().iloc[-1]

        # Exponential Moving Averages
        for period in [20, 50]:
            if len(df) >= period:
                mas[f"ema_{period}"] = df["close"].ewm(span=period).mean().iloc[-1]

        return mas

    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate trend strength (-100 to 100)"""
        if len(df) < 20:
            return 0

        # Use R-squared of linear regression with direction
        x = np.arange(len(df))
        z = np.polyfit(x, df["close"].values, 1)
        slope = z[0]
        p = np.poly1d(z)

        y_pred = p(x)
        y_actual = df["close"].values

        ss_res = np.sum((y_actual - y_pred) ** 2)
        ss_tot = np.sum((y_actual - np.mean(y_actual)) ** 2)

        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        strength = r_squared * 100

        # Apply direction: negative for downtrends, positive for uptrends
        if slope < 0:
            strength = -strength

        return max(-100, min(100, strength))

    def _calculate_trend_score(self, df: pd.DataFrame) -> float:
        """Calculate overall trend score (-100 to 100)"""
        if len(df) < 20:
            return 0

        # Combine multiple indicators
        score = 0

        # Price vs moving averages
        current = df["close"].iloc[-1]

        if len(df) >= 20:
            ma20 = df["close"].rolling(20).mean().iloc[-1]
            score += 25 if current > ma20 else -25

        if len(df) >= 50:
            ma50 = df["close"].rolling(50).mean().iloc[-1]
            score += 25 if current > ma50 else -25

        # Trend direction
        trend = self._calculate_trend(df)
        if trend == "uptrend":
            score += 50
        elif trend == "downtrend":
            score -= 50

        return score

    def _generate_trend_signals(self, df: pd.DataFrame) -> List[str]:
        """Generate trend-based signals"""
        signals = []

        trend = self._calculate_trend(df)
        strength = abs(self._calculate_trend_strength(df))

        if trend == "uptrend":
            if strength > 70:
                signals.append("Strong bullish uptrend detected")
            else:
                signals.append("Bullish uptrend in progress")
        elif trend == "downtrend":
            if strength > 70:
                signals.append("Strong bearish downtrend detected")
            else:
                signals.append("Bearish downtrend in progress")
        elif trend == "sideways":
            signals.append("Market ranging sideways")

        # Add crossover signals if available
        mas = self._calculate_moving_averages(df)
        if len(df) >= 50 and "ma_20" in mas and "ma_50" in mas:
            if mas["ma_20"] > mas["ma_50"]:
                signals.append("Short MA above long MA - bullish")
            else:
                signals.append("Short MA below long MA - bearish")

        return signals

    def _calculate_linear_regression(self, df: pd.DataFrame) -> Dict:
        """Calculate linear regression analysis"""
        if len(df) < 10:
            return {"slope": 0, "intercept": 0, "r_squared": 0, "prediction": 0}

        x = np.arange(len(df))
        y = df["close"].values
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)

        y_pred = p(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Predict next value
        next_x = len(df)
        prediction = p(next_x)

        return {
            "slope": float(z[0]),
            "intercept": float(z[1]),
            "r_squared": max(0, min(1, r_squared)),
            "prediction": float(prediction),
        }

    def _detect_trend_changes(self, df: pd.DataFrame) -> List[Dict]:
        """Detect trend changes in the data"""
        changes = []

        if len(df) < 30:
            return changes

        # Use rolling windows to detect trend changes
        window_size = min(20, len(df) // 4)
        trends = []

        for i in range(window_size, len(df), window_size // 2):
            window_data = df["close"].iloc[i - window_size : i]
            x = np.arange(len(window_data))
            slope = np.polyfit(x, window_data.values, 1)[0]

            if slope > 0.1:
                trends.append(("uptrend", i))
            elif slope < -0.1:
                trends.append(("downtrend", i))
            else:
                trends.append(("sideways", i))

        # Find changes
        for i in range(1, len(trends)):
            if trends[i][0] != trends[i - 1][0]:
                changes.append(
                    {
                        "position": trends[i][1],
                        "from_trend": trends[i - 1][0],
                        "to_trend": trends[i][0],
                    }
                )

        return changes[-5:]  # Return last 5 changes

    def _detect_ma_crossovers(self, df: pd.DataFrame) -> Dict:
        """Detect moving average crossovers"""
        crossovers = {"golden_cross": None, "death_cross": None}

        if len(df) < 50:
            return crossovers

        ma20 = df["close"].rolling(20).mean()
        ma50 = df["close"].rolling(50).mean()

        # Look for recent crossovers (last 10 periods)
        for i in range(len(df) - 10, len(df)):
            if i > 0:
                # Golden cross: 20MA crosses above 50MA
                if ma20.iloc[i] > ma50.iloc[i] and ma20.iloc[i - 1] <= ma50.iloc[i - 1]:
                    crossovers["golden_cross"] = {
                        "position": i,
                        "type": "golden_cross",
                        "ma20": ma20.iloc[i],
                        "ma50": ma50.iloc[i],
                    }

                # Death cross: 20MA crosses below 50MA
                elif (
                    ma20.iloc[i] < ma50.iloc[i] and ma20.iloc[i - 1] >= ma50.iloc[i - 1]
                ):
                    crossovers["death_cross"] = {
                        "position": i,
                        "type": "death_cross",
                        "ma20": ma20.iloc[i],
                        "ma50": ma50.iloc[i],
                    }

        return crossovers

    def _calculate_trend_channel(self, df: pd.DataFrame) -> Dict:
        """Calculate trend channel boundaries"""
        if len(df) < 20:
            return {
                "upper_channel": 0,
                "lower_channel": 0,
                "channel_width": 0,
                "position_in_channel": 0.5,
            }

        # Simple trend channel using linear regression and standard deviation
        x = np.arange(len(df))
        y = df["close"].values
        z = np.polyfit(x, y, 1)
        trend_line = np.poly1d(z)(x)

        # Calculate residuals
        residuals = y - trend_line
        std_dev = np.std(residuals)

        # Channel boundaries
        upper_channel = trend_line[-1] + (2 * std_dev)
        lower_channel = trend_line[-1] - (2 * std_dev)
        channel_width = upper_channel - lower_channel

        current_price = df["close"].iloc[-1]
        position_in_channel = (
            (current_price - lower_channel) / channel_width
            if channel_width > 0
            else 0.5
        )

        return {
            "upper_channel": float(upper_channel),
            "lower_channel": float(lower_channel),
            "channel_width": float(channel_width),
            "position_in_channel": max(0, min(1, position_in_channel)),
        }

    def _analyze_higher_timeframe_trend(self, df: pd.DataFrame) -> Dict:
        """Analyze higher timeframe trend alignment"""
        if len(df) < 50:
            return {"trend": "insufficient_data", "strength": 0, "alignment": "neutral"}

        # Simulate higher timeframe by using different periods
        short_trend = self._calculate_trend(df.tail(20))  # Short-term
        medium_trend = self._calculate_trend(df.tail(50))  # Medium-term
        long_trend = self._calculate_trend(df)  # Long-term

        trends = [short_trend, medium_trend, long_trend]

        # Check alignment
        if all(t == "uptrend" for t in trends):
            alignment = "bullish_aligned"
            strength = 90
        elif all(t == "downtrend" for t in trends):
            alignment = "bearish_aligned"
            strength = 90
        elif trends.count("uptrend") > trends.count("downtrend"):
            alignment = "bullish_mixed"
            strength = 60
        elif trends.count("downtrend") > trends.count("uptrend"):
            alignment = "bearish_mixed"
            strength = 60
        else:
            alignment = "neutral"
            strength = 30

        return {
            "trend": long_trend,
            "strength": strength,
            "alignment": alignment,
        }

    def _calculate_trend_consistency(self, df: pd.DataFrame) -> float:
        """Calculate how consistent the trend is (0-1)"""
        if len(df) < 20:
            return 0

        # Calculate R-squared as consistency measure
        x = np.arange(len(df))
        y = df["close"].values
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)

        y_pred = p(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        return max(0, min(1, r_squared))

    def _calculate_trend_momentum(self, df: pd.DataFrame) -> float:
        """Calculate trend momentum"""
        if len(df) < 10:
            return 0

        # Compare recent slope vs older slope
        recent_data = df["close"].tail(10)
        older_data = (
            df["close"].iloc[-20:-10] if len(df) >= 20 else df["close"].head(10)
        )

        recent_slope = np.polyfit(np.arange(len(recent_data)), recent_data.values, 1)[0]
        older_slope = np.polyfit(np.arange(len(older_data)), older_data.values, 1)[0]

        # Momentum is the change in slope
        momentum = recent_slope - older_slope

        # Normalize to reasonable range
        return float(np.clip(momentum * 10, -100, 100))
