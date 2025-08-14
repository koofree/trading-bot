"""
Candlestick Pattern Processor
Identifies candlestick patterns and formations
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .base import BasePreprocessor, PreprocessorResult


class CandlestickProcessor(BasePreprocessor):
    """Processes candlestick data to identify patterns and key levels"""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize candlestick processor"""
        super().__init__(config)
        self.name = "candlestick"

    def validate_input(self, data: Any) -> bool:
        """Validate that input is a list of candle dictionaries"""
        if not isinstance(data, list) or len(data) == 0:
            return False

        required_fields = ["open", "high", "low", "close"]
        return all(all(field in candle for field in required_fields) for candle in data)

    def process(self, candles: List[Dict]) -> PreprocessorResult:
        """Process candlestick data to identify patterns"""
        df = pd.DataFrame(candles)

        # Calculate basic candlestick metrics
        metrics = self._calculate_candlestick_metrics(df)

        # Identify patterns
        patterns = self._identify_patterns(df)

        # Find support and resistance levels
        levels = self._find_key_levels(df)

        # Generate signals based on patterns
        signals = self._generate_pattern_signals(patterns, df)

        return PreprocessorResult(
            processor_name=self.name,
            timestamp=datetime.now(),
            data={
                "patterns": patterns,
                "support_resistance": levels,
                "current_candle": self._analyze_current_candle(df.iloc[-1]),
                "candle_strength": self._calculate_candle_strength(df),
            },
            metrics=metrics,
            signals=signals,
            metadata={
                "total_candles": len(df),
                "timeframe": self.config.get("timeframe", "unknown"),
            },
        )

    def _calculate_candlestick_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate basic candlestick metrics"""
        current = df.iloc[-1]

        # Body size percentage
        body_size = abs(current["close"] - current["open"])
        full_range = current["high"] - current["low"]
        body_ratio = self._safe_divide(body_size, full_range, 0)

        # Upper and lower shadows
        if current["close"] > current["open"]:  # Bullish candle
            upper_shadow = current["high"] - current["close"]
            lower_shadow = current["open"] - current["low"]
        else:  # Bearish candle
            upper_shadow = current["high"] - current["open"]
            lower_shadow = current["close"] - current["low"]

        return {
            "body_size": body_size,
            "body_ratio": body_ratio,
            "upper_shadow": upper_shadow,
            "lower_shadow": lower_shadow,
            "full_range": full_range,
            "average_range": df["high"].sub(df["low"]).mean(),
            "current_vs_average_range": self._safe_divide(
                full_range, df["high"].sub(df["low"]).mean()
            ),
        }

    def _identify_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Identify candlestick patterns"""
        patterns = []

        if len(df) >= 3:
            # Check last 3 candles for patterns
            last3 = df.tail(3)

            # Doji
            if self._is_doji(last3.iloc[-1]):
                patterns.append(
                    {
                        "name": "doji",
                        "type": "reversal",
                        "strength": "medium",
                        "position": len(df) - 1,
                    }
                )

            # Hammer/Hanging Man
            hammer = self._is_hammer(last3.iloc[-1], last3.iloc[-2])
            if hammer:
                patterns.append(hammer)

            # Engulfing patterns
            engulfing = self._is_engulfing(last3.iloc[-2], last3.iloc[-1])
            if engulfing:
                patterns.append(engulfing)

            # Three white soldiers / Three black crows
            if len(df) >= 3:
                trend_pattern = self._is_three_pattern(df.tail(3))
                if trend_pattern:
                    patterns.append(trend_pattern)

        return patterns

    def _is_doji(self, candle: pd.Series) -> bool:
        """Check if candle is a doji"""
        body_size = abs(candle["close"] - candle["open"])
        full_range = candle["high"] - candle["low"]

        if full_range == 0:
            return False

        # Doji if body is less than 10% of full range
        return (body_size / full_range) < 0.1

    def _is_hammer(self, candle: pd.Series, prev_candle: pd.Series) -> Optional[Dict]:
        """Check for hammer or hanging man pattern"""
        body_size = abs(candle["close"] - candle["open"])
        full_range = candle["high"] - candle["low"]

        if full_range == 0:
            return None

        # Calculate shadows
        if candle["close"] > candle["open"]:  # Bullish
            upper_shadow = candle["high"] - candle["close"]
            lower_shadow = candle["open"] - candle["low"]
        else:  # Bearish
            upper_shadow = candle["high"] - candle["open"]
            lower_shadow = candle["close"] - candle["low"]

        # Hammer: small body at top, long lower shadow
        # More lenient criteria: lower shadow should be at least 2x body, upper shadow should be small
        if lower_shadow > body_size * 2 and upper_shadow < body_size:
            # Check trend context
            if prev_candle["close"] < prev_candle["open"]:  # After downtrend
                return {
                    "name": "hammer",
                    "type": "reversal_bullish",
                    "strength": "strong",
                    "position": -1,
                }
            else:  # After uptrend
                return {
                    "name": "hanging_man",
                    "type": "reversal_bearish",
                    "strength": "medium",
                    "position": -1,
                }

        return None

    def _is_engulfing(self, prev: pd.Series, current: pd.Series) -> Optional[Dict]:
        """Check for engulfing patterns"""
        prev_body = abs(prev["close"] - prev["open"])
        curr_body = abs(current["close"] - current["open"])

        # Bullish engulfing
        if (
            prev["close"] < prev["open"]
            and current["close"] > current["open"]  # Previous was bearish
            and current["open"] <= prev["close"]  # Current is bullish
            and current["close"] >= prev["open"]  # Opens below prev close
        ):  # Closes above prev open
            return {
                "name": "bullish_engulfing",
                "type": "reversal_bullish",
                "strength": "strong",
                "position": -1,
            }

        # Bearish engulfing
        if (
            prev["close"] > prev["open"]
            and current["close"] < current["open"]  # Previous was bullish
            and current["open"] >= prev["close"]  # Current is bearish
            and current["close"] <= prev["open"]  # Opens above prev close
        ):  # Closes below prev open
            return {
                "name": "bearish_engulfing",
                "type": "reversal_bearish",
                "strength": "strong",
                "position": -1,
            }

        return None

    def _is_three_pattern(self, last3: pd.DataFrame) -> Optional[Dict]:
        """Check for three white soldiers or three black crows"""
        all_bullish = all(last3["close"] > last3["open"])
        all_bearish = all(last3["close"] < last3["open"])

        if all_bullish:
            # Check if each candle closes higher than previous
            if (
                last3.iloc[1]["close"] > last3.iloc[0]["close"]
                and last3.iloc[2]["close"] > last3.iloc[1]["close"]
            ):
                return {
                    "name": "three_white_soldiers",
                    "type": "continuation_bullish",
                    "strength": "very_strong",
                    "position": -1,
                }

        if all_bearish:
            # Check if each candle closes lower than previous
            if (
                last3.iloc[1]["close"] < last3.iloc[0]["close"]
                and last3.iloc[2]["close"] < last3.iloc[1]["close"]
            ):
                return {
                    "name": "three_black_crows",
                    "type": "continuation_bearish",
                    "strength": "very_strong",
                    "position": -1,
                }

        return None

    def _find_key_levels(self, df: pd.DataFrame) -> Dict:
        """Find support and resistance levels"""
        # Use recent highs and lows
        recent_highs = df["high"].rolling(window=20).max()
        recent_lows = df["low"].rolling(window=20).min()

        # Current levels
        current_price = df["close"].iloc[-1]

        # Find nearest support (recent lows below current price)
        supports = recent_lows[recent_lows < current_price].dropna()
        nearest_support = supports.iloc[-1] if len(supports) > 0 else df["low"].min()

        # Find nearest resistance (recent highs above current price)
        resistances = recent_highs[recent_highs > current_price].dropna()
        nearest_resistance = (
            resistances.iloc[-1] if len(resistances) > 0 else df["high"].max()
        )

        return {
            "support": nearest_support,
            "resistance": nearest_resistance,
            "pivot": (df["high"].iloc[-1] + df["low"].iloc[-1] + df["close"].iloc[-1])
            / 3,
            "support_2": df["low"].rolling(window=50).min().iloc[-1]
            if len(df) >= 50
            else df["low"].min(),
            "resistance_2": df["high"].rolling(window=50).max().iloc[-1]
            if len(df) >= 50
            else df["high"].max(),
        }

    def _analyze_current_candle(self, candle: pd.Series) -> Dict:
        """Analyze the current candle characteristics"""
        body = candle["close"] - candle["open"]

        return {
            "type": "bullish" if body > 0 else "bearish" if body < 0 else "neutral",
            "body_size": abs(body),
            "body_percentage": abs(body) / candle["open"] * 100,
            "range": candle["high"] - candle["low"],
            "upper_wick": candle["high"] - max(candle["open"], candle["close"]),
            "lower_wick": min(candle["open"], candle["close"]) - candle["low"],
            "close_position": (candle["close"] - candle["low"])
            / (candle["high"] - candle["low"])
            if candle["high"] != candle["low"]
            else 0.5,
        }

    def _calculate_candle_strength(self, df: pd.DataFrame) -> Dict:
        """Calculate overall candle strength indicators"""
        # Count bullish vs bearish candles
        bullish_count = sum(df["close"] > df["open"])
        bearish_count = sum(df["close"] < df["open"])
        neutral_count = sum(df["close"] == df["open"])

        # Average body size
        body_sizes = abs(df["close"] - df["open"])
        avg_body = body_sizes.mean()

        # Trend strength (using linear regression on close prices)
        if len(df) >= 5:
            x = np.arange(len(df))
            z = np.polyfit(x, df["close"].values, 1)
            trend_slope = z[0]
            trend_strength = abs(trend_slope) / df["close"].mean() * 100
        else:
            trend_slope = 0
            trend_strength = 0

        return {
            "bullish_ratio": bullish_count / len(df),
            "bearish_ratio": bearish_count / len(df),
            "average_body_size": avg_body,
            "trend_slope": trend_slope,
            "trend_strength": trend_strength,
            "momentum": "bullish"
            if trend_slope > 0
            else "bearish"
            if trend_slope < 0
            else "neutral",
        }

    def _generate_pattern_signals(
        self, patterns: List[Dict], df: pd.DataFrame
    ) -> List[str]:
        """Generate trading signals based on identified patterns"""
        signals = []

        for pattern in patterns:
            if pattern["type"] == "reversal_bullish":
                signals.append(f"Bullish reversal pattern detected: {pattern['name']}")
            elif pattern["type"] == "reversal_bearish":
                signals.append(f"Bearish reversal pattern detected: {pattern['name']}")
            elif pattern["type"] == "continuation_bullish":
                signals.append(f"Bullish continuation pattern: {pattern['name']}")
            elif pattern["type"] == "continuation_bearish":
                signals.append(f"Bearish continuation pattern: {pattern['name']}")

        # Add support/resistance signals
        current_price = df["close"].iloc[-1]
        support = self._find_key_levels(df)["support"]
        resistance = self._find_key_levels(df)["resistance"]

        if current_price <= support * 1.01:  # Within 1% of support
            signals.append("Price near support level")
        elif current_price >= resistance * 0.99:  # Within 1% of resistance
            signals.append("Price near resistance level")

        return signals
