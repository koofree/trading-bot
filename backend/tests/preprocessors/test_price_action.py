"""
Test Suite for Price Action Processor
Tests price action analysis, breakouts, and key levels
"""

import unittest
from typing import Dict, List

import numpy as np

from services.preprocessors import PriceActionProcessor


class TestPriceActionProcessor(unittest.TestCase):
    """Test price action analysis"""

    def setUp(self):
        """Set up test data"""
        self.processor = PriceActionProcessor()

        # Generate different market scenarios
        self.trending_data = self._generate_trending_data()
        self.ranging_data = self._generate_ranging_data()
        self.breakout_data = self._generate_breakout_data()
        self.pullback_data = self._generate_pullback_data()

    def _generate_trending_data(self) -> List[Dict]:
        """Generate trending market data"""
        data = []
        base_price = 100

        for i in range(50):
            # Uptrend with some noise
            trend = i * 0.5
            noise = np.random.randn() * 1

            open_price = base_price + trend + noise
            close_price = open_price + np.random.randn() * 2

            data.append({
                "open": open_price,
                "high": max(open_price, close_price) + abs(np.random.randn() * 0.5),
                "low": min(open_price, close_price) - abs(np.random.randn() * 0.5),
                "close": close_price,
                "volume": 1000 + np.random.randint(-100, 100)
            })

            base_price = close_price

        return data

    def _generate_ranging_data(self) -> List[Dict]:
        """Generate ranging/consolidating market data"""
        data = []
        center_price = 100

        for i in range(50):
            # Oscillate around center with defined range
            oscillation = np.sin(i * 0.3) * 5
            noise = np.random.randn() * 1

            open_price = center_price + oscillation + noise
            close_price = open_price + np.random.randn() * 2

            data.append({
                "open": open_price,
                "high": max(open_price, close_price) + abs(np.random.randn() * 0.5),
                "low": min(open_price, close_price) - abs(np.random.randn() * 0.5),
                "close": close_price,
                "volume": 1000 + np.random.randint(-100, 100)
            })

        return data

    def _generate_breakout_data(self) -> List[Dict]:
        """Generate data with breakout pattern"""
        data = []

        # Consolidation phase
        for i in range(30):
            price = 100 + np.random.randn() * 2
            data.append({
                "open": price,
                "high": price + 1,
                "low": price - 1,
                "close": price + np.random.randn() * 0.5,
                "volume": 1000
            })

        # Breakout phase
        for i in range(20):
            price = 105 + i * 0.8  # Strong upward movement
            data.append({
                "open": price,
                "high": price + 2,
                "low": price - 0.5,
                "close": price + 1.5,
                "volume": 2000 + i * 100  # Increasing volume
            })

        return data

    def _generate_pullback_data(self) -> List[Dict]:
        """Generate data with pullback pattern"""
        data = []
        base_price = 100

        # Initial uptrend
        for i in range(20):
            price = base_price + i * 0.7
            data.append({
                "open": price,
                "high": price + 1,
                "low": price - 0.5,
                "close": price + 0.5,
                "volume": 1000
            })

        # Pullback
        for i in range(10):
            price = 114 - i * 0.4  # Gentle pullback
            data.append({
                "open": price,
                "high": price + 0.5,
                "low": price - 1,
                "close": price - 0.3,
                "volume": 800
            })

        # Resume uptrend
        for i in range(20):
            price = 110 + i * 0.6
            data.append({
                "open": price,
                "high": price + 1,
                "low": price - 0.3,
                "close": price + 0.7,
                "volume": 1200
            })

        return data

    def test_validate_input(self):
        """Test input validation"""
        self.assertTrue(self.processor.validate_input(self.trending_data))
        self.assertFalse(self.processor.validate_input([]))
        self.assertFalse(self.processor.validate_input("not a list"))
        self.assertFalse(self.processor.validate_input([{"open": 100}]))  # Missing fields

    def test_breakout_detection(self):
        """Test breakout pattern detection"""
        result = self.processor.process(self.breakout_data)

        self.assertTrue(result.is_valid())
        self.assertIn("breakouts", result.data)

        breakouts = result.data["breakouts"]
        self.assertIsInstance(breakouts, dict)

        # Should detect at least one type of breakout
        self.assertTrue(
            breakouts.get("resistance_break") or
            breakouts.get("support_break") or
            breakouts.get("range_break"),
            "Should detect some form of breakout"
        )

    def test_support_resistance_identification(self):
        """Test identification of support and resistance levels"""
        result = self.processor.process(self.ranging_data)

        self.assertIn("key_levels", result.data)
        levels = result.data["key_levels"]

        self.assertIn("strong_resistance", levels)
        self.assertIn("strong_support", levels)
        self.assertIn("weak_resistance", levels)
        self.assertIn("weak_support", levels)

        # Strong support should be below strong resistance
        if levels["strong_support"] and levels["strong_resistance"]:
            self.assertLess(levels["strong_support"], levels["strong_resistance"])

    def test_fibonacci_levels(self):
        """Test Fibonacci retracement level calculation"""
        result = self.processor.process(self.pullback_data)

        self.assertIn("fibonacci", result.data)
        fib = result.data["fibonacci"]

        # Check standard Fibonacci levels
        expected_levels = ["0.0", "0.236", "0.382", "0.5", "0.618", "0.786", "1.0"]
        for level in expected_levels:
            self.assertIn(level, fib, f"Should include Fibonacci level {level}")

        # Levels should be in ascending order
        fib_values = [fib[level] for level in expected_levels if level in fib]
        self.assertEqual(fib_values, sorted(fib_values))

    def test_price_patterns(self):
        """Test price pattern recognition"""
        result = self.processor.process(self.trending_data)

        self.assertIn("patterns", result.data)
        patterns = result.data["patterns"]

        self.assertIsInstance(patterns, list)

        # Check pattern structure if patterns exist
        if patterns:
            pattern = patterns[0]
            self.assertIn("type", pattern)
            self.assertIn("strength", pattern)
            self.assertIn("location", pattern)

    def test_range_analysis(self):
        """Test price range analysis"""
        result = self.processor.process(self.ranging_data)

        self.assertIn("range_analysis", result.data)
        range_info = result.data["range_analysis"]

        self.assertIn("range_high", range_info)
        self.assertIn("range_low", range_info)
        self.assertIn("range_width", range_info)
        self.assertIn("current_position", range_info)

        # Range width should be positive
        self.assertGreater(range_info["range_width"], 0)

        # Current position should be between 0 and 1
        self.assertGreaterEqual(range_info["current_position"], 0)
        self.assertLessEqual(range_info["current_position"], 1)

    def test_pullback_detection(self):
        """Test pullback detection in trending markets"""
        result = self.processor.process(self.pullback_data)

        self.assertIn("pullback_analysis", result.data)
        pullback = result.data["pullback_analysis"]

        self.assertIn("is_pullback", pullback)
        self.assertIn("pullback_depth", pullback)
        self.assertIn("pullback_level", pullback)

    def test_price_action_signals(self):
        """Test signal generation based on price action"""
        result = self.processor.process(self.breakout_data)

        signals = result.signals
        self.assertIsInstance(signals, list)

        # Breakout data should generate at least one signal
        self.assertGreater(len(signals), 0, "Breakout should generate signals")

        # Check for breakout-related signals
        breakout_signal_found = any(
            "breakout" in s.lower() or "break" in s.lower()
            for s in signals
        )
        self.assertTrue(breakout_signal_found, "Should have breakout-related signals")

    def test_metrics_calculation(self):
        """Test price action metrics"""
        result = self.processor.process(self.trending_data)

        metrics = result.metrics

        self.assertIn("price_range", metrics)
        self.assertIn("price_change", metrics)
        self.assertIn("price_momentum", metrics)

        # All metrics should be finite numbers
        for key, value in metrics.items():
            self.assertTrue(np.isfinite(value), f"Metric {key} should be finite")

    def test_swing_points(self):
        """Test identification of swing highs and lows"""
        result = self.processor.process(self.ranging_data)

        self.assertIn("swing_points", result.data)
        swings = result.data["swing_points"]

        self.assertIn("swing_highs", swings)
        self.assertIn("swing_lows", swings)

        # Should identify multiple swing points in ranging market
        self.assertGreater(len(swings["swing_highs"]), 0, "Should find swing highs")
        self.assertGreater(len(swings["swing_lows"]), 0, "Should find swing lows")

    def test_error_handling(self):
        """Test error handling with invalid data"""
        # Test with invalid data structure
        bad_data = [{"invalid": "data"}]
        result = self.processor.preprocess(bad_data)

        self.assertFalse(result.is_valid())
        self.assertGreater(len(result.errors), 0)

        # Test with insufficient data
        small_data = self.trending_data[:2]
        result = self.processor.process(small_data)

        # Should still process but with limited analysis
        self.assertIsNotNone(result)
        self.assertIn("key_levels", result.data)


if __name__ == "__main__":
    unittest.main()
