"""
Market Data Preprocessor Service
Fetches and processes market data from multiple sources to provide enriched, accurate metrics
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MarketDataPreprocessor:
    """Preprocesses raw market data into enriched metrics for analysis"""

    def __init__(self, upbit_connector):
        self.upbit = upbit_connector

    def get_enriched_market_data(self, market: str) -> Dict:
        """
        Fetch and process market data to create enriched metrics

        Returns a dictionary with:
        - Current price and 24h price changes
        - Volume metrics (24h, average, ratio)
        - Price levels (high, low, support, resistance)
        - Trend indicators
        - Volatility metrics
        """
        try:
            # Fetch multiple data sources
            logger.info(f"Fetching enriched data for {market}")

            # Get ticker for current 24h stats
            ticker_data = self._fetch_ticker(market)

            # Get candles for historical analysis
            candles_1h = self.upbit.get_candles(
                market, "minutes", 60, 24
            )  # 24 hours of hourly
            candles_5m = self.upbit.get_candles(
                market, "minutes", 5, 100
            )  # Recent 5-min candles

            # Process the data
            enriched_data = self._process_market_data(
                market, ticker_data, candles_1h, candles_5m
            )

            logger.info(
                f"Enriched data prepared for {market}: {list(enriched_data.keys())}"
            )
            return enriched_data

        except Exception as e:
            logger.error(f"Error preprocessing market data for {market}: {e}")
            return self._get_default_market_data(market)

    def _fetch_ticker(self, market: str) -> Optional[Dict]:
        """Fetch current ticker data"""
        try:
            tickers = self.upbit.get_ticker([market])
            if tickers and len(tickers) > 0:
                return tickers[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching ticker for {market}: {e}")
            return None

    def _process_market_data(
        self,
        market: str,
        ticker: Optional[Dict],
        candles_1h: List[Dict],
        candles_5m: List[Dict],
    ) -> Dict:
        """Process raw data into enriched metrics"""

        result = {
            "market": market,
            "timestamp": datetime.now().isoformat(),
        }

        # Process ticker data if available
        if ticker:
            result.update(self._process_ticker_data(ticker))

        # Process candle data
        if candles_1h:
            result.update(self._process_candle_data(candles_1h, "24h"))

        if candles_5m:
            result.update(self._process_recent_trend(candles_5m))

        # Calculate additional metrics
        result.update(self._calculate_derived_metrics(result))

        return result

    def _process_ticker_data(self, ticker: Dict) -> Dict:
        """Extract and process ticker information"""

        # Upbit ticker fields:
        # trade_price: current price
        # opening_price: 24h ago price
        # high_price: 24h high
        # low_price: 24h low
        # prev_closing_price: previous day close
        # change: RISE/FALL/EVEN
        # change_price: absolute change
        # change_rate: percentage change (0.0132 = 1.32%)
        # acc_trade_volume_24h: 24h volume in base currency
        # acc_trade_price_24h: 24h volume in quote currency (KRW)

        current_price = ticker.get("trade_price", 0)
        opening_price = ticker.get("opening_price", current_price)

        return {
            "current_price": current_price,
            "price_24h_ago": opening_price,
            "high_24h": ticker.get("high_price", current_price),
            "low_24h": ticker.get("low_price", current_price),
            "prev_closing_price": ticker.get("prev_closing_price", current_price),
            # Price changes
            "price_change_24h": ticker.get("change_rate", 0)
            * 100,  # Convert to percentage
            "price_change_amount": ticker.get("change_price", 0),
            "price_change_direction": ticker.get("change", "EVEN"),
            # Volume (properly formatted)
            "volume_24h_base": ticker.get(
                "acc_trade_volume_24h", 0
            ),  # e.g., ETH amount
            "volume_24h_quote": ticker.get(
                "acc_trade_price_24h", 0
            ),  # e.g., KRW amount
            # Additional info
            "signed_change_price": ticker.get("signed_change_price", 0),
            "signed_change_rate": ticker.get("signed_change_rate", 0) * 100,
        }

    def _process_candle_data(self, candles: List[Dict], period: str) -> Dict:
        """Process candle data for a given period"""

        if not candles:
            return {}

        df = pd.DataFrame(candles)

        # Calculate aggregated metrics
        result = {}

        if "trade_price" in df.columns:
            result[f"avg_price_{period}"] = df["trade_price"].mean()
            result[f"price_std_{period}"] = df["trade_price"].std()

            # Calculate actual high/low from candles
            if "high_price" in df.columns:
                result[f"high_{period}_actual"] = df["high_price"].max()
            if "low_price" in df.columns:
                result[f"low_{period}_actual"] = df["low_price"].min()

        if "candle_acc_trade_volume" in df.columns:
            result[f"avg_volume_{period}"] = df["candle_acc_trade_volume"].mean()
            result[f"total_volume_{period}"] = df["candle_acc_trade_volume"].sum()

            # Volume trend
            recent_volume = (
                df["candle_acc_trade_volume"].iloc[:6].mean()
            )  # Last 6 periods
            older_volume = (
                df["candle_acc_trade_volume"].iloc[-6:].mean()
            )  # First 6 periods

            if older_volume > 0:
                result[f"volume_trend_{period}"] = (
                    (recent_volume - older_volume) / older_volume * 100
                )
            else:
                result[f"volume_trend_{period}"] = 0

        return result

    def _process_recent_trend(self, candles_5m: List[Dict]) -> Dict:
        """Analyze recent price trend from 5-minute candles"""

        if not candles_5m or len(candles_5m) < 10:
            return {"trend_1h": "unknown", "trend_strength": 0}

        df = pd.DataFrame(candles_5m[:12])  # Last hour (12 x 5min)

        if "trade_price" not in df.columns:
            return {"trend_1h": "unknown", "trend_strength": 0}

        prices = df["trade_price"].values

        # Simple linear regression for trend
        x = np.arange(len(prices))
        z = np.polyfit(x, prices, 1)
        slope = z[0]

        # Normalize slope to percentage
        avg_price = prices.mean()
        trend_percentage = (slope * len(prices)) / avg_price * 100

        # Determine trend
        if trend_percentage > 0.5:
            trend = "up"
        elif trend_percentage < -0.5:
            trend = "down"
        else:
            trend = "sideways"

        return {
            "trend_1h": trend,
            "trend_strength": abs(trend_percentage),
            "recent_high": prices.max(),
            "recent_low": prices.min(),
        }

    def _calculate_derived_metrics(self, data: Dict) -> Dict:
        """Calculate additional derived metrics"""

        result = {}

        # Volatility calculation
        if "high_24h" in data and "low_24h" in data and "current_price" in data:
            if data["current_price"] > 0:
                result["volatility_24h"] = (
                    (data["high_24h"] - data["low_24h"]) / data["current_price"] * 100
                )

        # Volume ratio (current vs average)
        if "volume_24h_base" in data and "avg_volume_24h" in data:
            if data.get("avg_volume_24h", 0) > 0:
                result["volume_ratio"] = (
                    data["volume_24h_base"] / data["avg_volume_24h"]
                )
            else:
                result["volume_ratio"] = 1.0

        # Support and resistance (simple calculation)
        if "low_24h" in data and "high_24h" in data:
            result["support_level"] = data["low_24h"]
            result["resistance_level"] = data["high_24h"]

            # Mid-point
            result["pivot_point"] = (data["high_24h"] + data["low_24h"]) / 2

        # Price position within range
        if all(k in data for k in ["current_price", "low_24h", "high_24h"]):
            price_range = data["high_24h"] - data["low_24h"]
            if price_range > 0:
                result["price_position"] = (
                    (data["current_price"] - data["low_24h"]) / price_range * 100
                )
            else:
                result["price_position"] = 50  # Middle if no range

        # Trading suggestion based on metrics
        result["momentum"] = self._calculate_momentum(data)

        return result

    def _calculate_momentum(self, data: Dict) -> str:
        """Calculate overall momentum from various metrics"""

        score = 0

        # Price change contribution
        if "price_change_24h" in data:
            if data["price_change_24h"] > 3:
                score += 2
            elif data["price_change_24h"] > 1:
                score += 1
            elif data["price_change_24h"] < -3:
                score -= 2
            elif data["price_change_24h"] < -1:
                score -= 1

        # Volume contribution
        if "volume_ratio" in data:
            if data.get("volume_ratio", 1) > 1.5:
                score += 1
            elif data.get("volume_ratio", 1) < 0.5:
                score -= 1

        # Trend contribution
        if "trend_1h" in data:
            if data["trend_1h"] == "up":
                score += 1
            elif data["trend_1h"] == "down":
                score -= 1

        # Convert score to momentum
        if score >= 3:
            return "strong_bullish"
        elif score >= 1:
            return "bullish"
        elif score <= -3:
            return "strong_bearish"
        elif score <= -1:
            return "bearish"
        else:
            return "neutral"

    def _get_default_market_data(self, market: str) -> Dict:
        """Return default market data when fetching fails"""

        return {
            "market": market,
            "timestamp": datetime.now().isoformat(),
            "current_price": 0,
            "price_24h_ago": 0,
            "price_change_24h": 0,
            "price_change_amount": 0,
            "high_24h": 0,
            "low_24h": 0,
            "volume_24h_base": 0,
            "volume_24h_quote": 0,
            "trend_1h": "unknown",
            "momentum": "neutral",
            "error": "Failed to fetch market data",
        }

    def format_for_llm(self, data: Dict) -> str:
        """Format market data for LLM consumption"""

        if not data or "error" in data:
            return "Market data unavailable"

        # Create human-readable summary
        lines = [
            f"Market: {data.get('market', 'Unknown')}",
            f"Current Price: {data.get('current_price', 0):,.0f} KRW",
            f"24h Change: {data.get('price_change_24h', 0):.2f}% ({data.get('price_change_amount', 0):+,.0f} KRW)",
            f"24h High: {data.get('high_24h', 0):,.0f} KRW",
            f"24h Low: {data.get('low_24h', 0):,.0f} KRW",
            f"24h Volume: {data.get('volume_24h_base', 0):.4f} ({data.get('volume_24h_quote', 0)/1e9:.2f}B KRW)",
            f"Volume Ratio: {data.get('volume_ratio', 1):.2f}x average",
            f"Volatility: {data.get('volatility_24h', 0):.2f}%",
            f"1h Trend: {data.get('trend_1h', 'unknown')} ({data.get('trend_strength', 0):.2f}% strength)",
            f"Momentum: {data.get('momentum', 'neutral')}",
            f"Price Position: {data.get('price_position', 50):.0f}% of 24h range",
        ]

        return "\n".join(lines)
