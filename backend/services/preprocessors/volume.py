"""
Volume Analysis Processor
Analyzes volume patterns and volume-price relationships
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .base import BasePreprocessor, PreprocessorResult


class VolumeProcessor(BasePreprocessor):
    """Processes volume data to identify patterns and anomalies"""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize volume processor"""
        super().__init__(config)
        self.name = "volume"

    def validate_input(self, data: Any) -> bool:
        """Validate that input contains volume data"""
        if not isinstance(data, list) or len(data) == 0:
            return False

        required_fields = ["volume", "close"]
        return all(all(field in item for field in required_fields) for item in data)

    def process(self, data: List[Dict]) -> PreprocessorResult:
        """Process volume data to identify patterns"""
        df = pd.DataFrame(data)

        # Calculate volume metrics
        metrics = self._calculate_volume_metrics(df)

        # Analyze volume patterns
        patterns = self._analyze_volume_patterns(df)

        # Calculate volume indicators
        indicators = self._calculate_volume_indicators(df)

        # Generate volume-based signals
        signals = self._generate_volume_signals(df, patterns, indicators)

        return PreprocessorResult(
            processor_name=self.name,
            timestamp=datetime.now(),
            data={
                "patterns": patterns,
                "indicators": indicators,
                "volume_profile": self._calculate_volume_profile(df),
                "price_volume_correlation": self._calculate_pv_correlation(df),
            },
            metrics=metrics,
            signals=signals,
            metadata={"total_periods": len(df), "total_volume": df["volume"].sum()},
        )

    def _calculate_volume_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate basic volume metrics"""
        current_volume = df["volume"].iloc[-1]
        avg_volume = df["volume"].mean()

        # Volume moving averages
        vol_ma_5 = (
            df["volume"].rolling(5).mean().iloc[-1] if len(df) >= 5 else avg_volume
        )
        vol_ma_20 = (
            df["volume"].rolling(20).mean().iloc[-1] if len(df) >= 20 else avg_volume
        )

        # Volume statistics
        return {
            "current_volume": current_volume,
            "average_volume": avg_volume,
            "volume_ratio": self._safe_divide(current_volume, avg_volume, 1.0),
            "volume_ma5": vol_ma_5,
            "volume_ma20": vol_ma_20,
            "volume_std": df["volume"].std(),
            "volume_zscore": self._safe_divide(
                current_volume - avg_volume, df["volume"].std(), 0
            ),
            "max_volume": df["volume"].max(),
            "min_volume": df["volume"].min(),
            "volume_percentile": (df["volume"] <= current_volume).mean() * 100,
        }

    def _analyze_volume_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze volume patterns"""
        patterns = {}

        # Volume trend
        if len(df) >= 10:
            recent_avg = df["volume"].tail(5).mean()
            older_avg = df["volume"].iloc[-10:-5].mean()

            if recent_avg > older_avg * 1.2:
                patterns["volume_trend"] = "increasing"
                patterns["trend_strength"] = (recent_avg / older_avg - 1) * 100
            elif recent_avg < older_avg * 0.8:
                patterns["volume_trend"] = "decreasing"
                patterns["trend_strength"] = (1 - recent_avg / older_avg) * 100
            else:
                patterns["volume_trend"] = "stable"
                patterns["trend_strength"] = 0

        # Volume spikes
        patterns["spikes"] = self._detect_volume_spikes(df)

        # Volume dry-ups
        patterns["dryups"] = self._detect_volume_dryups(df)

        # Accumulation/Distribution phases
        patterns["phase"] = self._detect_accumulation_distribution(df)

        return patterns

    def _calculate_volume_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate volume-based technical indicators"""
        indicators = {}

        # On-Balance Volume (OBV)
        obv = self._calculate_obv(df)
        indicators["obv"] = obv.iloc[-1]
        indicators["obv_trend"] = (
            "up"
            if obv.iloc[-1] > obv.iloc[-5]
            else "down"
            if len(obv) >= 5
            else "neutral"
        )

        # Volume-Weighted Average Price (VWAP)
        vwap = self._calculate_vwap(df)
        indicators["vwap"] = vwap
        indicators["price_vs_vwap"] = (
            (df["close"].iloc[-1] / vwap - 1) * 100 if vwap > 0 else 0
        )

        # Money Flow Index (MFI) - simplified version
        mfi = self._calculate_mfi(df)
        indicators["mfi"] = mfi

        # Volume Rate of Change
        vroc = self._calculate_vroc(df)
        indicators["vroc"] = vroc

        # Accumulation/Distribution Line
        adl = self._calculate_adl(df)
        indicators["adl"] = adl.iloc[-1] if len(adl) > 0 else 0
        indicators["adl_trend"] = self._get_trend(adl)

        return indicators

    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume"""
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = df["volume"].iloc[0]

        for i in range(1, len(df)):
            if df["close"].iloc[i] > df["close"].iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] + df["volume"].iloc[i]
            elif df["close"].iloc[i] < df["close"].iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] - df["volume"].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i - 1]

        return obv

    def _calculate_vwap(self, df: pd.DataFrame) -> float:
        """Calculate Volume-Weighted Average Price"""
        if df["volume"].sum() == 0:
            return 0

        typical_price = (
            (df["high"] + df["low"] + df["close"]) / 3
            if "high" in df.columns
            else df["close"]
        )
        return (typical_price * df["volume"]).sum() / df["volume"].sum()

    def _calculate_mfi(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Money Flow Index (simplified)"""
        if len(df) < period or "high" not in df.columns:
            return 50  # Neutral value

        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        money_flow = typical_price * df["volume"]

        positive_flow = 0
        negative_flow = 0

        for i in range(1, min(period + 1, len(df))):
            if typical_price.iloc[-i] > typical_price.iloc[-i - 1]:
                positive_flow += money_flow.iloc[-i]
            else:
                negative_flow += money_flow.iloc[-i]

        if negative_flow == 0:
            return 100

        money_ratio = positive_flow / negative_flow
        mfi = 100 - (100 / (1 + money_ratio))

        return mfi

    def _calculate_vroc(self, df: pd.DataFrame, period: int = 10) -> float:
        """Calculate Volume Rate of Change"""
        if len(df) <= period:
            return 0

        current_vol = df["volume"].iloc[-1]
        past_vol = df["volume"].iloc[-period - 1]

        if past_vol == 0:
            return 0

        return ((current_vol - past_vol) / past_vol) * 100

    def _calculate_adl(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Accumulation/Distribution Line"""
        if "high" not in df.columns or "low" not in df.columns:
            return pd.Series([0] * len(df))

        # Money Flow Multiplier
        mfm = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / (
            df["high"] - df["low"]
        )
        mfm = mfm.fillna(0)  # Handle division by zero

        # Money Flow Volume
        mfv = mfm * df["volume"]

        # Accumulation/Distribution Line
        adl = mfv.cumsum()

        return adl

    def _detect_volume_spikes(self, df: pd.DataFrame) -> List[Dict]:
        """Detect unusual volume spikes"""
        spikes = []
        avg_volume = df["volume"].mean()
        std_volume = df["volume"].std()

        for i in range(len(df)):
            if df["volume"].iloc[i] > avg_volume + (2 * std_volume):
                spike_info = {
                    "index": i,
                    "volume": df["volume"].iloc[i],
                    "ratio": df["volume"].iloc[i] / avg_volume,
                    "price_change": self._calculate_percentage_change(
                        df["close"].iloc[i - 1] if i > 0 else df["close"].iloc[i],
                        df["close"].iloc[i],
                    ),
                }

                # Classify spike type
                if spike_info["price_change"] > 1:
                    spike_info["type"] = "bullish_spike"
                elif spike_info["price_change"] < -1:
                    spike_info["type"] = "bearish_spike"
                else:
                    spike_info["type"] = "neutral_spike"

                spikes.append(spike_info)

        return spikes[-5:]  # Return last 5 spikes

    def _detect_volume_dryups(self, df: pd.DataFrame) -> List[Dict]:
        """Detect periods of unusually low volume"""
        dryups = []
        avg_volume = df["volume"].mean()

        for i in range(len(df)):
            if df["volume"].iloc[i] < avg_volume * 0.5:
                dryups.append(
                    {
                        "index": i,
                        "volume": df["volume"].iloc[i],
                        "ratio": df["volume"].iloc[i] / avg_volume,
                    }
                )

        return dryups[-5:]  # Return last 5 dry-ups

    def _detect_accumulation_distribution(self, df: pd.DataFrame) -> str:
        """Detect accumulation or distribution phase"""
        if len(df) < 20:
            return "insufficient_data"

        recent = df.tail(20)

        # Check price trend
        price_trend = recent["close"].iloc[-1] > recent["close"].iloc[0]

        # Check volume trend
        vol_first_half = recent["volume"].iloc[:10].mean()
        vol_second_half = recent["volume"].iloc[10:].mean()
        volume_increasing = vol_second_half > vol_first_half

        # Determine phase
        if price_trend and volume_increasing:
            return "accumulation"  # Buying pressure
        elif not price_trend and volume_increasing:
            return "distribution"  # Selling pressure
        elif price_trend and not volume_increasing:
            return "markup"  # Price rise on low volume
        else:
            return "markdown"  # Price fall on low volume

    def _calculate_volume_profile(self, df: pd.DataFrame) -> Dict:
        """Calculate volume profile (volume at price levels)"""
        if len(df) < 10:
            return {}

        # Create price bins
        price_range = df["close"].max() - df["close"].min()
        n_bins = min(10, len(df) // 2)

        if price_range == 0:
            return {"single_price": df["close"].iloc[0]}

        bins = np.linspace(df["close"].min(), df["close"].max(), n_bins + 1)

        # Calculate volume at each price level
        profile = {}
        for i in range(len(bins) - 1):
            mask = (df["close"] >= bins[i]) & (df["close"] < bins[i + 1])
            level_volume = df.loc[mask, "volume"].sum()

            profile[f"level_{i}"] = {
                "price_range": f"{bins[i]:.2f}-{bins[i+1]:.2f}",
                "volume": level_volume,
                "percentage": (level_volume / df["volume"].sum()) * 100
                if df["volume"].sum() > 0
                else 0,
            }

        # Find Point of Control (POC) - price level with highest volume
        poc_level = max(profile.items(), key=lambda x: x[1]["volume"])

        # Extract numeric POC price (middle of range)
        price_range_str = poc_level[1]["price_range"]
        low_price, high_price = map(float, price_range_str.split("-"))
        poc_price = (low_price + high_price) / 2

        return {
            "profile": profile,
            "poc": poc_price,
            "poc_range": poc_level[1]["price_range"],
            "poc_volume": poc_level[1]["volume"],
        }

    def _calculate_pv_correlation(self, df: pd.DataFrame) -> float:
        """Calculate price-volume correlation"""
        if len(df) < 5:
            return 0

        # Calculate correlation between price changes and volume
        price_changes = df["close"].pct_change()

        # Remove NaN values
        valid_mask = ~(price_changes.isna())

        if valid_mask.sum() < 2:
            return 0

        correlation = price_changes[valid_mask].corr(df["volume"][valid_mask])

        return correlation if not pd.isna(correlation) else 0

    def _get_trend(self, series: pd.Series) -> str:
        """Determine trend from a series"""
        if len(series) < 5:
            return "neutral"

        recent = series.iloc[-5:].mean()
        older = (
            series.iloc[-10:-5].mean() if len(series) >= 10 else series.iloc[:-5].mean()
        )

        if recent > older * 1.05:
            return "up"
        elif recent < older * 0.95:
            return "down"
        else:
            return "neutral"

    def _generate_volume_signals(
        self, df: pd.DataFrame, patterns: Dict, indicators: Dict
    ) -> List[str]:
        """Generate trading signals based on volume analysis"""
        signals = []

        # Volume trend signals
        if patterns.get("volume_trend") == "increasing":
            if patterns.get("trend_strength", 0) > 50:
                signals.append("Strong volume increase detected")
        elif patterns.get("volume_trend") == "decreasing":
            signals.append("Volume drying up - potential reversal")

        # Volume spike signals
        if patterns.get("spikes"):
            recent_spikes = [s for s in patterns["spikes"] if s["index"] >= len(df) - 5]
            for spike in recent_spikes:
                if spike["type"] == "bullish_spike":
                    signals.append(
                        f"Bullish volume spike: {spike['ratio']:.1f}x average"
                    )
                elif spike["type"] == "bearish_spike":
                    signals.append(
                        f"Bearish volume spike: {spike['ratio']:.1f}x average"
                    )

        # Accumulation/Distribution signals
        phase = patterns.get("phase")
        if phase == "accumulation":
            signals.append("Accumulation phase detected - bullish")
        elif phase == "distribution":
            signals.append("Distribution phase detected - bearish")

        # Indicator-based signals
        if indicators.get("mfi", 50) > 80:
            signals.append("MFI overbought (>80)")
        elif indicators.get("mfi", 50) < 20:
            signals.append("MFI oversold (<20)")

        if indicators.get("price_vs_vwap", 0) > 2:
            signals.append("Price significantly above VWAP")
        elif indicators.get("price_vs_vwap", 0) < -2:
            signals.append("Price significantly below VWAP")

        return signals
