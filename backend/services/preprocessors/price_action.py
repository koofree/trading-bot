"""
Price Action Processor
Analyzes price movements and key price levels
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from .base import BasePreprocessor, PreprocessorResult


class PriceActionProcessor(BasePreprocessor):
    """Analyzes price action for trading signals"""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize price action processor"""
        super().__init__(config)
        self.name = "price_action"

    def validate_input(self, data: Any) -> bool:
        """Validate input data"""
        if not isinstance(data, list) or len(data) == 0:
            return False
        return "close" in data[0]

    def process(self, data: List[Dict]) -> PreprocessorResult:
        """Process price action data"""
        df = pd.DataFrame(data)

        metrics = self._calculate_price_metrics(df)
        levels = self._find_price_levels(df)
        breakouts = self._detect_breakouts(df, levels)
        structure = self._analyze_market_structure(df)

        signals = self._generate_price_signals(df, levels, breakouts, structure)

        return PreprocessorResult(
            processor_name=self.name,
            timestamp=datetime.now(),
            data={
                "key_levels": levels,
                "breakouts": breakouts,
                "market_structure": structure,
                "fibonacci": levels.get("fibonacci", {}),
                "range_analysis": self._analyze_price_range(df),
                "pullback_analysis": self._analyze_pullbacks(df),
                "patterns": self._identify_price_patterns(df),
                "swing_points": self._find_swing_points(df),
            },
            metrics=metrics,
            signals=signals,
        )

    def _calculate_price_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate price-based metrics"""
        current = df["close"].iloc[-1]

        return {
            "price_range": df["close"].max() - df["close"].min(),
            "price_change": (current - df["close"].iloc[0]) / df["close"].iloc[0] * 100
            if len(df) > 1
            else 0,
            "price_momentum": self._calculate_price_velocity(df),
            "current_price": current,
        }

    def _find_price_levels(self, df: pd.DataFrame) -> Dict:
        """Find key price levels using various methods"""
        levels = {}

        # Fibonacci levels
        if "high" in df and "low" in df:
            high = df["high"].max()
            low = df["low"].min()
            diff = high - low

            levels["fibonacci"] = {
                "0.0": low,
                "0.236": low + diff * 0.236,
                "0.382": low + diff * 0.382,
                "0.5": low + diff * 0.5,
                "0.618": low + diff * 0.618,
                "0.786": low + diff * 0.786,
                "1.0": high,
            }

        # Psychological levels (round numbers)
        current = df["close"].iloc[-1]
        round_level = round(current, -3)  # Round to nearest 1000

        levels["psychological"] = {
            "below": round_level - 1000,
            "current": round_level,
            "above": round_level + 1000,
        }

        # Volume-weighted levels
        if "volume" in df:
            vwap = (df["close"] * df["volume"]).sum() / df["volume"].sum()
            levels["vwap"] = vwap

        # Recent highs and lows
        levels["recent"] = {
            "high_24h": df["high"].tail(24).max()
            if "high" in df and len(df) >= 24
            else current,
            "low_24h": df["low"].tail(24).min()
            if "low" in df and len(df) >= 24
            else current,
            "high_7d": df["high"].tail(168).max()
            if "high" in df and len(df) >= 168
            else current,
            "low_7d": df["low"].tail(168).min()
            if "low" in df and len(df) >= 168
            else current,
        }

        # Support and resistance levels expected by tests
        levels["strong_resistance"] = df["high"].max() if "high" in df else current
        levels["strong_support"] = df["low"].min() if "low" in df else current
        levels["weak_resistance"] = (
            df["close"].quantile(0.75) if len(df) > 4 else current
        )
        levels["weak_support"] = df["close"].quantile(0.25) if len(df) > 4 else current

        return levels

    def _detect_breakouts(self, df: pd.DataFrame, levels: Dict) -> Dict:
        """Detect price breakouts from key levels"""
        breakouts = {
            "resistance_break": None,
            "support_break": None,
            "range_break": None,
        }
        current = df["close"].iloc[-1]

        # Check recent high/low breakouts (more sensitive)
        if "recent" in levels:
            resistance_level = levels["recent"]["high_24h"]
            support_level = levels["recent"]["low_24h"]

            # Break above recent highs (allow small margin)
            if current > resistance_level * 0.999:  # 0.1% margin
                breakouts["resistance_break"] = {
                    "level": resistance_level,
                    "strength": (current - resistance_level) / resistance_level * 100,
                    "current_price": current,
                }

            # Break below recent lows
            if current < support_level * 1.001:  # 0.1% margin
                breakouts["support_break"] = {
                    "level": support_level,
                    "strength": (support_level - current) / support_level * 100,
                    "current_price": current,
                }

        # Additional breakout detection based on price movement
        if len(df) >= 10:
            # Check if current price broke out of recent range
            recent_high = (
                df["high"].tail(10).max()
                if "high" in df
                else df["close"].tail(10).max()
            )
            recent_low = (
                df["low"].tail(10).min() if "low" in df else df["close"].tail(10).min()
            )

            if current > recent_high and not breakouts["resistance_break"]:
                breakouts["resistance_break"] = {
                    "level": recent_high,
                    "strength": (current - recent_high) / recent_high * 100,
                    "current_price": current,
                }

            if current < recent_low and not breakouts["support_break"]:
                breakouts["support_break"] = {
                    "level": recent_low,
                    "strength": (recent_low - current) / recent_low * 100,
                    "current_price": current,
                }

        # Check for range breakout (price moving significantly outside typical range)
        if len(df) >= 20:
            # Check if we've broken out of the consolidation range
            first_half = df["close"][: len(df) // 2]
            second_half = df["close"][len(df) // 2 :]

            first_half_avg = first_half.mean()
            second_half_avg = second_half.mean()

            # If second half average is significantly different, it's likely a breakout
            percentage_change = (
                abs(second_half_avg - first_half_avg) / first_half_avg * 100
            )

            if percentage_change > 2:  # 2% change indicates breakout
                breakouts["range_break"] = {
                    "type": "trend_breakout",
                    "magnitude": percentage_change,
                    "direction": "up" if second_half_avg > first_half_avg else "down",
                }

        # Simple fallback - if we see significant price movement, call it a breakout
        if len(df) >= 5 and not any(breakouts.values()):
            price_start = df["close"].iloc[:5].mean()
            price_end = df["close"].iloc[-5:].mean()
            change = abs(price_end - price_start) / price_start * 100

            if change > 1:  # 1% change is a breakout
                if price_end > price_start:
                    breakouts["resistance_break"] = {
                        "level": price_start,
                        "strength": change,
                        "current_price": price_end,
                    }
                else:
                    breakouts["support_break"] = {
                        "level": price_start,
                        "strength": change,
                        "current_price": price_end,
                    }

        return breakouts

    def _analyze_market_structure(self, df: pd.DataFrame) -> Dict:
        """Analyze overall market structure"""
        if len(df) < 20:
            return {"trend": "insufficient_data"}

        # Find swing highs and lows
        highs = []
        lows = []

        for i in range(1, len(df) - 1):
            if "high" in df:
                # Swing high
                if (
                    df["high"].iloc[i] > df["high"].iloc[i - 1]
                    and df["high"].iloc[i] > df["high"].iloc[i + 1]
                ):
                    highs.append({"index": i, "price": df["high"].iloc[i]})

                # Swing low
                if (
                    df["low"].iloc[i] < df["low"].iloc[i - 1]
                    and df["low"].iloc[i] < df["low"].iloc[i + 1]
                ):
                    lows.append({"index": i, "price": df["low"].iloc[i]})

        # Determine structure
        structure = "ranging"

        if len(highs) >= 2 and len(lows) >= 2:
            # Higher highs and higher lows = uptrend
            if (
                highs[-1]["price"] > highs[-2]["price"]
                and lows[-1]["price"] > lows[-2]["price"]
            ):
                structure = "uptrend"
            # Lower highs and lower lows = downtrend
            elif (
                highs[-1]["price"] < highs[-2]["price"]
                and lows[-1]["price"] < lows[-2]["price"]
            ):
                structure = "downtrend"

        return {
            "structure": structure,
            "swing_highs": highs[-3:] if highs else [],
            "swing_lows": lows[-3:] if lows else [],
        }

    def _analyze_price_waves(self, df: pd.DataFrame) -> Dict:
        """Analyze price waves using Elliott Wave principles (simplified)"""
        if len(df) < 50:
            return {"wave_count": "insufficient_data"}

        # Simplified wave detection
        prices = df["close"].values

        # Find local maxima and minima
        from scipy.signal import find_peaks

        peaks, _ = find_peaks(prices, distance=5)
        troughs, _ = find_peaks(-prices, distance=5)

        waves = []
        for i in range(len(peaks) - 1):
            wave_height = prices[peaks[i + 1]] - prices[peaks[i]]
            waves.append(
                {
                    "start": int(peaks[i]),
                    "end": int(peaks[i + 1]),
                    "height": float(wave_height),
                    "type": "impulse" if wave_height > 0 else "corrective",
                }
            )

        return {
            "wave_count": len(waves),
            "recent_waves": waves[-5:] if waves else [],
            "dominant_wave": "bullish"
            if sum(w["height"] for w in waves) > 0
            else "bearish"
            if waves
            else "neutral",
        }

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        if "high" not in df or "low" not in df or len(df) < period:
            return 0

        high_low = df["high"] - df["low"]
        high_close = abs(df["high"] - df["close"].shift())
        low_close = abs(df["low"] - df["close"].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)

        return true_range.rolling(period).mean().iloc[-1]

    def _calculate_price_velocity(self, df: pd.DataFrame) -> float:
        """Calculate rate of price change"""
        if len(df) < 2:
            return 0

        # Simple velocity: change over last 5 periods
        periods = min(5, len(df) - 1)
        return (df["close"].iloc[-1] - df["close"].iloc[-periods - 1]) / periods

    def _calculate_price_acceleration(self, df: pd.DataFrame) -> float:
        """Calculate acceleration of price change"""
        if len(df) < 10:
            return 0

        # Calculate velocity at two points
        v1 = (df["close"].iloc[-5] - df["close"].iloc[-10]) / 5
        v2 = (df["close"].iloc[-1] - df["close"].iloc[-5]) / 5

        # Acceleration is change in velocity
        return v2 - v1

    def _generate_price_signals(
        self, df: pd.DataFrame, levels: Dict, breakouts: List, structure: Dict
    ) -> List[str]:
        """Generate signals based on price action"""
        signals = []

        # Structure signals
        if structure.get("structure") == "uptrend":
            signals.append("Market in uptrend - higher highs and higher lows")
        elif structure.get("structure") == "downtrend":
            signals.append("Market in downtrend - lower highs and lower lows")

        # Breakout signals
        if breakouts.get("resistance_break"):
            level = breakouts["resistance_break"]["level"]
            signals.append(f"Resistance breakout at {level:.2f}")

        if breakouts.get("support_break"):
            level = breakouts["support_break"]["level"]
            signals.append(f"Support breakdown at {level:.2f}")

        if breakouts.get("range_break"):
            direction = breakouts["range_break"]["direction"]
            signals.append(f"Range breakout to the {direction}")

        # Level proximity signals
        current = df["close"].iloc[-1]
        if "fibonacci" in levels:
            for fib_level, price in levels["fibonacci"].items():
                if abs(current - price) / price < 0.01:  # Within 1%
                    signals.append(f"Price near Fibonacci {fib_level}% level")

        return signals

    def _analyze_price_range(self, df: pd.DataFrame) -> Dict:
        """Analyze price range characteristics"""
        if len(df) < 10:
            return {
                "range_high": 0,
                "range_low": 0,
                "range_width": 0,
                "current_position": 0.5,
            }

        range_high = df["close"].max()
        range_low = df["close"].min()
        range_width = range_high - range_low
        current = df["close"].iloc[-1]

        current_position = (
            (current - range_low) / range_width if range_width > 0 else 0.5
        )

        return {
            "range_high": range_high,
            "range_low": range_low,
            "range_width": range_width,
            "current_position": current_position,
        }

    def _analyze_pullbacks(self, df: pd.DataFrame) -> Dict:
        """Analyze pullback patterns"""
        if len(df) < 20:
            return {"is_pullback": False, "pullback_depth": 0, "pullback_level": None}

        # Simple pullback detection: recent decline after uptrend
        recent_high = df["close"].tail(20).max()
        current = df["close"].iloc[-1]
        pullback_depth = (recent_high - current) / recent_high * 100

        return {
            "is_pullback": pullback_depth > 2,  # 2% decline
            "pullback_depth": pullback_depth,
            "pullback_level": recent_high,
        }

    def _identify_price_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Identify price patterns"""
        patterns = []

        if len(df) >= 20:
            # Simple trend pattern
            first_half_avg = df["close"][: len(df) // 2].mean()
            second_half_avg = df["close"][len(df) // 2 :].mean()

            if second_half_avg > first_half_avg * 1.02:
                patterns.append(
                    {"type": "uptrend", "strength": "medium", "location": len(df) - 1}
                )
            elif second_half_avg < first_half_avg * 0.98:
                patterns.append(
                    {"type": "downtrend", "strength": "medium", "location": len(df) - 1}
                )

        return patterns

    def _find_swing_points(self, df: pd.DataFrame) -> Dict:
        """Find swing highs and lows"""
        swing_highs = []
        swing_lows = []

        if len(df) >= 5 and "high" in df and "low" in df:
            for i in range(2, len(df) - 2):
                # Swing high: higher than neighbors
                if (
                    df["high"].iloc[i] > df["high"].iloc[i - 1]
                    and df["high"].iloc[i] > df["high"].iloc[i + 1]
                ):
                    swing_highs.append({"index": i, "price": df["high"].iloc[i]})

                # Swing low: lower than neighbors
                if (
                    df["low"].iloc[i] < df["low"].iloc[i - 1]
                    and df["low"].iloc[i] < df["low"].iloc[i + 1]
                ):
                    swing_lows.append({"index": i, "price": df["low"].iloc[i]})

        return {
            "swing_highs": swing_highs[-10:],  # Last 10 swing highs
            "swing_lows": swing_lows[-10:],  # Last 10 swing lows
        }
