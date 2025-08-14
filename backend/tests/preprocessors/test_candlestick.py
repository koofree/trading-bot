"""
Test Suite for Candlestick Pattern Processor
Tests candlestick pattern recognition and analysis
"""

import unittest
from typing import Dict, List

import numpy as np

from services.preprocessors import CandlestickProcessor


class TestCandlestickProcessor(unittest.TestCase):
    """Test candlestick pattern recognition"""

    def setUp(self):
        """Set up test data"""
        self.processor = CandlestickProcessor()

        # Create sample candlestick data
        self.sample_candles = self._generate_sample_candles()

        # Create specific pattern data
        self.doji_candles = self._generate_doji_pattern()
        self.hammer_candles = self._generate_hammer_pattern()
        self.engulfing_candles = self._generate_engulfing_pattern()

    def _generate_sample_candles(self) -> List[Dict]:
        """Generate sample candlestick data"""
        candles = []
        base_price = 100

        for i in range(50):
            open_price = base_price + np.random.randn() * 2
            close_price = open_price + np.random.randn() * 3
            high_price = max(open_price, close_price) + abs(np.random.randn())
            low_price = min(open_price, close_price) - abs(np.random.randn())

            candles.append(
                {
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": 1000 + np.random.randint(0, 500),
                }
            )

            base_price = close_price

        return candles

    def _generate_doji_pattern(self) -> List[Dict]:
        """Generate candles with a doji at the end"""
        candles = self._generate_sample_candles()[:10]

        # Add a doji candle
        last_close = candles[-1]["close"]
        candles.append(
            {
                "open": last_close,
                "high": last_close + 2,
                "low": last_close - 2,
                "close": last_close + 0.1,  # Very small body
                "volume": 1500,
            }
        )

        return candles

    def _generate_hammer_pattern(self) -> List[Dict]:
        """Generate candles with a hammer pattern"""
        candles = []

        # Create downtrend
        price = 100
        for _i in range(5):
            candles.append(
                {
                    "open": price,
                    "high": price + 1,
                    "low": price - 2,
                    "close": price - 1.5,
                    "volume": 1000,
                }
            )
            price -= 2

        # Add hammer
        candles.append(
            {
                "open": price,
                "high": price + 0.5,
                "low": price - 4,  # Long lower shadow
                "close": price + 0.3,  # Small bullish body
                "volume": 1500,
            }
        )

        return candles

    def _generate_engulfing_pattern(self) -> List[Dict]:
        """Generate bullish engulfing pattern"""
        candles = []

        # Some normal candles
        for i in range(5):
            candles.append(
                {
                    "open": 100 + i,
                    "high": 101 + i,
                    "low": 99 + i,
                    "close": 100.5 + i,
                    "volume": 1000,
                }
            )

        # Small bearish candle
        candles.append(
            {"open": 105, "high": 105.5, "low": 103, "close": 103.5, "volume": 800}
        )

        # Large bullish candle (engulfing)
        candles.append(
            {
                "open": 103,  # Opens below previous close
                "high": 107,
                "low": 102.5,
                "close": 106,  # Closes above previous open
                "volume": 1500,
            }
        )

        return candles

    def test_validate_input(self):
        """Test input validation"""
        # Valid input
        self.assertTrue(self.processor.validate_input(self.sample_candles))

        # Invalid inputs
        self.assertFalse(self.processor.validate_input([]))
        self.assertFalse(self.processor.validate_input("not a list"))
        self.assertFalse(
            self.processor.validate_input([{"open": 100}])
        )  # Missing fields

    def test_process_basic(self):
        """Test basic processing"""
        result = self.processor.process(self.sample_candles)

        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid())
        self.assertIn("patterns", result.data)
        self.assertIn("support_resistance", result.data)
        self.assertIn("current_candle", result.data)

    def test_doji_detection(self):
        """Test doji pattern detection"""
        result = self.processor.process(self.doji_candles)

        patterns = result.data["patterns"]
        doji_found = any(p["name"] == "doji" for p in patterns)

        self.assertTrue(doji_found, "Doji pattern should be detected")

    def test_hammer_detection(self):
        """Test hammer pattern detection"""
        result = self.processor.process(self.hammer_candles)

        patterns = result.data["patterns"]
        hammer_found = any(p["name"] == "hammer" for p in patterns)

        self.assertTrue(hammer_found, "Hammer pattern should be detected")

    def test_engulfing_detection(self):
        """Test engulfing pattern detection"""
        result = self.processor.process(self.engulfing_candles)

        patterns = result.data["patterns"]
        engulfing_found = any("engulfing" in p["name"] for p in patterns)

        self.assertTrue(engulfing_found, "Engulfing pattern should be detected")

    def test_support_resistance_levels(self):
        """Test support and resistance calculation"""
        result = self.processor.process(self.sample_candles)

        levels = result.data["support_resistance"]

        self.assertIn("support", levels)
        self.assertIn("resistance", levels)
        self.assertIn("pivot", levels)

        # Support should be below resistance
        self.assertLess(levels["support"], levels["resistance"])

    def test_candle_strength(self):
        """Test candle strength calculation"""
        result = self.processor.process(self.sample_candles)

        strength = result.data["candle_strength"]

        self.assertIn("bullish_ratio", strength)
        self.assertIn("bearish_ratio", strength)
        self.assertIn("momentum", strength)

        # Ratios should sum to approximately 1 (allowing for neutral candles)
        total_ratio = strength["bullish_ratio"] + strength["bearish_ratio"]
        self.assertLessEqual(total_ratio, 1.0)

    def test_current_candle_analysis(self):
        """Test current candle analysis"""
        result = self.processor.process(self.sample_candles)

        current = result.data["current_candle"]

        self.assertIn("type", current)
        self.assertIn("body_size", current)
        self.assertIn("body_percentage", current)
        self.assertIn("range", current)
        self.assertIn("upper_wick", current)
        self.assertIn("lower_wick", current)
        self.assertIn("close_position", current)

        # Close position should be between 0 and 1
        self.assertGreaterEqual(current["close_position"], 0)
        self.assertLessEqual(current["close_position"], 1)

    def test_metrics_calculation(self):
        """Test candlestick metrics calculation"""
        result = self.processor.process(self.sample_candles)

        metrics = result.metrics

        self.assertIn("body_size", metrics)
        self.assertIn("body_ratio", metrics)
        self.assertIn("upper_shadow", metrics)
        self.assertIn("lower_shadow", metrics)
        self.assertIn("full_range", metrics)
        self.assertIn("average_range", metrics)

        # All metrics should be non-negative
        for value in metrics.values():
            self.assertGreaterEqual(value, 0)

    def test_signal_generation(self):
        """Test trading signal generation"""
        # Test with data that should generate signals
        result = self.processor.process(self.hammer_candles)

        signals = result.signals
        self.assertIsInstance(signals, list)

        # Hammer pattern should generate a signal
        if result.data["patterns"]:
            self.assertGreater(len(signals), 0, "Patterns should generate signals")

    def test_error_handling(self):
        """Test error handling with invalid data"""
        # Test with invalid data structure
        bad_data = [{"invalid": "data"}]
        result = self.processor.preprocess(bad_data)

        self.assertFalse(result.is_valid())
        self.assertGreater(len(result.errors), 0)

        # Test with empty data
        empty_result = self.processor.preprocess([])
        self.assertFalse(empty_result.is_valid())


if __name__ == "__main__":
    unittest.main()
