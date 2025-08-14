"""
Test Suite for Trend Analysis Processor
Tests trend detection, moving averages, and trend strength
"""

import unittest
from typing import Dict, List

import numpy as np

from services.preprocessors import TrendProcessor


class TestTrendProcessor(unittest.TestCase):
    """Test trend analysis"""

    def setUp(self):
        """Set up test data"""
        self.processor = TrendProcessor()

        # Generate different trend scenarios
        self.uptrend_data = self._generate_uptrend()
        self.downtrend_data = self._generate_downtrend()
        self.sideways_data = self._generate_sideways()
        self.mixed_trend_data = self._generate_mixed_trend()

    def _generate_uptrend(self) -> List[Dict]:
        """Generate strong uptrend data"""
        data = []
        base_price = 100

        for i in range(100):
            # Strong uptrend with minor corrections
            trend = i * 0.8
            noise = np.random.randn() * 1.5
            correction = np.sin(i * 0.2) * 2  # Minor waves

            price = base_price + trend + noise + correction

            data.append({
                "open": price - 0.5,
                "high": price + 1,
                "low": price - 1,
                "close": price,
                "volume": 1000 + np.random.randint(-100, 100)
            })

        return data

    def _generate_downtrend(self) -> List[Dict]:
        """Generate strong downtrend data"""
        data = []
        base_price = 150

        for i in range(100):
            # Strong downtrend with minor rallies
            trend = -i * 0.6
            noise = np.random.randn() * 1.5
            rally = np.sin(i * 0.2) * 2  # Minor rallies

            price = base_price + trend + noise + rally

            data.append({
                "open": price + 0.5,
                "high": price + 1,
                "low": price - 1,
                "close": price,
                "volume": 1000 + np.random.randint(-100, 100)
            })

        return data

    def _generate_sideways(self) -> List[Dict]:
        """Generate sideways/ranging market data"""
        data = []
        center_price = 100

        for i in range(100):
            # Sideways movement with no clear trend
            oscillation = np.sin(i * 0.1) * 5
            noise = np.random.randn() * 2

            price = center_price + oscillation + noise

            data.append({
                "open": price,
                "high": price + 1.5,
                "low": price - 1.5,
                "close": price + np.random.randn() * 0.5,
                "volume": 1000 + np.random.randint(-100, 100)
            })

        return data

    def _generate_mixed_trend(self) -> List[Dict]:
        """Generate data with multiple trend changes"""
        data = []

        # Uptrend phase
        for i in range(30):
            price = 100 + i * 0.5
            data.append({
                "open": price,
                "high": price + 1,
                "low": price - 0.5,
                "close": price + 0.3,
                "volume": 1000
            })

        # Sideways phase
        for i in range(20):
            price = 115 + np.sin(i * 0.3) * 3
            data.append({
                "open": price,
                "high": price + 1,
                "low": price - 1,
                "close": price + np.random.randn() * 0.5,
                "volume": 1000
            })

        # Downtrend phase
        for i in range(30):
            price = 115 - i * 0.4
            data.append({
                "open": price,
                "high": price + 0.5,
                "low": price - 1,
                "close": price - 0.2,
                "volume": 1000
            })

        # Recovery phase
        for i in range(20):
            price = 103 + i * 0.3
            data.append({
                "open": price,
                "high": price + 1,
                "low": price - 0.3,
                "close": price + 0.2,
                "volume": 1000
            })

        return data

    def test_validate_input(self):
        """Test input validation"""
        self.assertTrue(self.processor.validate_input(self.uptrend_data))
        self.assertFalse(self.processor.validate_input([]))
        self.assertFalse(self.processor.validate_input("not a list"))
        self.assertFalse(self.processor.validate_input([{"open": 100}]))  # Missing close

    def test_trend_direction_detection(self):
        """Test trend direction identification"""
        # Test uptrend
        uptrend_result = self.processor.process(self.uptrend_data)
        self.assertIn("trend_direction", uptrend_result.data)
        self.assertEqual(uptrend_result.data["trend_direction"], "uptrend")

        # Test downtrend
        downtrend_result = self.processor.process(self.downtrend_data)
        self.assertEqual(downtrend_result.data["trend_direction"], "downtrend")

        # Test sideways
        sideways_result = self.processor.process(self.sideways_data)
        self.assertIn(sideways_result.data["trend_direction"], ["sideways", "neutral"])

    def test_moving_averages(self):
        """Test moving average calculations"""
        result = self.processor.process(self.uptrend_data)

        self.assertIn("moving_averages", result.data)
        ma = result.data["moving_averages"]

        # Check for different MA periods
        expected_mas = ["sma_20", "sma_50", "ema_20", "ema_50"]
        for ma_type in expected_mas:
            self.assertIn(ma_type, ma, f"Should calculate {ma_type}")
            self.assertIsInstance(ma[ma_type], (int, float))
            self.assertGreater(ma[ma_type], 0)

        # In uptrend, shorter MAs should be above longer MAs
        if "sma_20" in ma and "sma_50" in ma:
            self.assertGreaterEqual(ma["sma_20"], ma["sma_50"] * 0.95)  # Allow small margin

    def test_trend_strength(self):
        """Test trend strength calculation"""
        # Strong uptrend should have high positive strength
        uptrend_result = self.processor.process(self.uptrend_data)
        self.assertIn("trend_strength", uptrend_result.data)
        self.assertGreater(uptrend_result.data["trend_strength"], 50)

        # Strong downtrend should have high negative strength
        downtrend_result = self.processor.process(self.downtrend_data)
        self.assertLess(downtrend_result.data["trend_strength"], -50)

        # Sideways should have low strength
        sideways_result = self.processor.process(self.sideways_data)
        self.assertLess(abs(sideways_result.data["trend_strength"]), 30)

    def test_trend_metrics(self):
        """Test trend-related metrics"""
        result = self.processor.process(self.uptrend_data)

        metrics = result.metrics

        self.assertIn("trend_score", metrics)
        self.assertIn("trend_consistency", metrics)
        self.assertIn("trend_momentum", metrics)

        # Trend score should be between -100 and 100
        self.assertGreaterEqual(metrics["trend_score"], -100)
        self.assertLessEqual(metrics["trend_score"], 100)

        # Consistency should be between 0 and 1
        self.assertGreaterEqual(metrics["trend_consistency"], 0)
        self.assertLessEqual(metrics["trend_consistency"], 1)

    def test_trend_changes(self):
        """Test detection of trend changes"""
        result = self.processor.process(self.mixed_trend_data)

        self.assertIn("trend_changes", result.data)
        changes = result.data["trend_changes"]

        # Should detect multiple trend changes in mixed data
        self.assertGreater(len(changes), 0, "Should detect trend changes")

        # Check structure of trend changes
        if changes:
            change = changes[0]
            self.assertIn("position", change)
            self.assertIn("from_trend", change)
            self.assertIn("to_trend", change)

    def test_linear_regression(self):
        """Test linear regression trend analysis"""
        result = self.processor.process(self.uptrend_data)

        self.assertIn("linear_regression", result.data)
        lr = result.data["linear_regression"]

        self.assertIn("slope", lr)
        self.assertIn("intercept", lr)
        self.assertIn("r_squared", lr)
        self.assertIn("prediction", lr)

        # Slope should be positive for uptrend
        self.assertGreater(lr["slope"], 0)

        # R-squared should be between 0 and 1
        self.assertGreaterEqual(lr["r_squared"], 0)
        self.assertLessEqual(lr["r_squared"], 1)

    def test_trend_signals(self):
        """Test signal generation based on trend"""
        # Uptrend should generate bullish signals
        uptrend_result = self.processor.process(self.uptrend_data)
        uptrend_signals = uptrend_result.signals

        self.assertIsInstance(uptrend_signals, list)
        bullish_signal = any("bullish" in s.lower() or "uptrend" in s.lower()
                            for s in uptrend_signals)
        self.assertTrue(bullish_signal, "Uptrend should generate bullish signals")

        # Downtrend should generate bearish signals
        downtrend_result = self.processor.process(self.downtrend_data)
        downtrend_signals = downtrend_result.signals

        bearish_signal = any("bearish" in s.lower() or "downtrend" in s.lower()
                            for s in downtrend_signals)
        self.assertTrue(bearish_signal, "Downtrend should generate bearish signals")

    def test_ma_crossovers(self):
        """Test moving average crossover detection"""
        result = self.processor.process(self.mixed_trend_data)

        self.assertIn("ma_crossovers", result.data)
        crossovers = result.data["ma_crossovers"]

        self.assertIn("golden_cross", crossovers)
        self.assertIn("death_cross", crossovers)

        # Mixed trend data might have crossovers
        if crossovers["golden_cross"] or crossovers["death_cross"]:
            # If crossover detected, check structure
            cross = crossovers["golden_cross"] or crossovers["death_cross"]
            self.assertIn("position", cross)
            self.assertIn("type", cross)

    def test_trend_channel(self):
        """Test trend channel identification"""
        result = self.processor.process(self.uptrend_data)

        self.assertIn("trend_channel", result.data)
        channel = result.data["trend_channel"]

        self.assertIn("upper_channel", channel)
        self.assertIn("lower_channel", channel)
        self.assertIn("channel_width", channel)
        self.assertIn("position_in_channel", channel)

        # Channel width should be positive
        self.assertGreater(channel["channel_width"], 0)

        # Position should be between 0 and 1
        self.assertGreaterEqual(channel["position_in_channel"], 0)
        self.assertLessEqual(channel["position_in_channel"], 1)

    def test_higher_timeframe_trend(self):
        """Test analysis of higher timeframe trends"""
        result = self.processor.process(self.uptrend_data)

        self.assertIn("higher_timeframe", result.data)
        htf = result.data["higher_timeframe"]

        self.assertIn("trend", htf)
        self.assertIn("strength", htf)
        self.assertIn("alignment", htf)

    def test_error_handling(self):
        """Test error handling with invalid data"""
        # Test with invalid data structure
        bad_data = [{"invalid": "data"}]
        result = self.processor.preprocess(bad_data)

        self.assertFalse(result.is_valid())
        self.assertGreater(len(result.errors), 0)

        # Test with insufficient data
        small_data = self.uptrend_data[:3]
        result = self.processor.process(small_data)

        # Should still process but with limited analysis
        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid())

    def test_minimum_data_requirements(self):
        """Test processor with minimum required data"""
        # Test with minimum viable dataset
        min_data = self.uptrend_data[:10]
        result = self.processor.process(min_data)

        self.assertIsNotNone(result)
        self.assertIn("trend_direction", result.data)
        self.assertIn("moving_averages", result.data)


if __name__ == "__main__":
    unittest.main()
