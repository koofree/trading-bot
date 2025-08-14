"""
Test Suite for Volatility Analysis Processor
Tests volatility measurements, Bollinger Bands, ATR, and volatility patterns
"""

import unittest
from typing import Dict, List

import numpy as np

from services.preprocessors import VolatilityProcessor


class TestVolatilityProcessor(unittest.TestCase):
    """Test volatility analysis"""

    def setUp(self):
        """Set up test data"""
        self.processor = VolatilityProcessor()

        # Generate different volatility scenarios
        self.low_volatility_data = self._generate_low_volatility()
        self.high_volatility_data = self._generate_high_volatility()
        self.increasing_volatility_data = self._generate_increasing_volatility()
        self.spike_volatility_data = self._generate_volatility_spike()

    def _generate_low_volatility(self) -> List[Dict]:
        """Generate low volatility market data"""
        data = []
        base_price = 100

        for i in range(100):
            # Small price movements
            trend = i * 0.1
            noise = np.random.randn() * 0.5  # Low volatility

            price = base_price + trend + noise

            data.append({
                "open": price,
                "high": price + 0.3,
                "low": price - 0.3,
                "close": price + np.random.randn() * 0.2,
                "volume": 1000
            })

        return data

    def _generate_high_volatility(self) -> List[Dict]:
        """Generate high volatility market data"""
        data = []
        base_price = 100

        for i in range(100):
            # Large price movements
            trend = i * 0.1
            noise = np.random.randn() * 5  # High volatility

            price = base_price + trend + noise

            data.append({
                "open": price,
                "high": price + abs(np.random.randn() * 3),
                "low": price - abs(np.random.randn() * 3),
                "close": price + np.random.randn() * 2,
                "volume": 1000 + abs(np.random.randn() * 500)
            })

        return data

    def _generate_increasing_volatility(self) -> List[Dict]:
        """Generate data with increasing volatility over time"""
        data = []
        base_price = 100

        for i in range(100):
            # Volatility increases over time
            volatility_factor = 0.5 + (i / 100) * 4
            trend = i * 0.1
            noise = np.random.randn() * volatility_factor

            price = base_price + trend + noise

            data.append({
                "open": price,
                "high": price + abs(np.random.randn() * volatility_factor),
                "low": price - abs(np.random.randn() * volatility_factor),
                "close": price + np.random.randn() * volatility_factor * 0.5,
                "volume": 1000
            })

        return data

    def _generate_volatility_spike(self) -> List[Dict]:
        """Generate data with volatility spike"""
        data = []
        base_price = 100

        for i in range(100):
            # Normal volatility with spike in the middle
            if 40 <= i <= 60:
                volatility = 5  # Spike period
            else:
                volatility = 1  # Normal period

            noise = np.random.randn() * volatility
            price = base_price + i * 0.1 + noise

            data.append({
                "open": price,
                "high": price + abs(np.random.randn() * volatility),
                "low": price - abs(np.random.randn() * volatility),
                "close": price + np.random.randn() * volatility * 0.3,
                "volume": 1000 if volatility == 1 else 2000
            })

        return data

    def test_validate_input(self):
        """Test input validation"""
        self.assertTrue(self.processor.validate_input(self.low_volatility_data))
        self.assertFalse(self.processor.validate_input([]))
        self.assertFalse(self.processor.validate_input("not a list"))
        self.assertFalse(self.processor.validate_input([{"open": 100}]))  # Missing fields

    def test_volatility_measurement(self):
        """Test basic volatility measurements"""
        # Low volatility should have lower values
        low_vol_result = self.processor.process(self.low_volatility_data)
        low_vol = low_vol_result.data["current_volatility"]

        # High volatility should have higher values
        high_vol_result = self.processor.process(self.high_volatility_data)
        high_vol = high_vol_result.data["current_volatility"]

        self.assertLess(low_vol, high_vol, "Low volatility should be less than high volatility")

        # Check volatility is positive
        self.assertGreater(low_vol, 0)
        self.assertGreater(high_vol, 0)

    def test_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        result = self.processor.process(self.low_volatility_data)

        self.assertIn("bollinger_bands", result.data)
        bb = result.data["bollinger_bands"]

        self.assertIn("upper", bb)
        self.assertIn("middle", bb)
        self.assertIn("lower", bb)
        self.assertIn("width", bb)
        self.assertIn("position", bb)

        # Bands should be in correct order
        self.assertGreater(bb["upper"], bb["middle"])
        self.assertGreater(bb["middle"], bb["lower"])

        # Width should be positive
        self.assertGreater(bb["width"], 0)

        # Position should be between 0 and 1
        self.assertGreaterEqual(bb["position"], 0)
        self.assertLessEqual(bb["position"], 1)

    def test_atr_calculation(self):
        """Test Average True Range calculation"""
        result = self.processor.process(self.high_volatility_data)

        self.assertIn("atr", result.data)
        atr = result.data["atr"]

        self.assertIn("current", atr)
        self.assertIn("average", atr)
        self.assertIn("percentile", atr)

        # ATR should be positive
        self.assertGreater(atr["current"], 0)
        self.assertGreater(atr["average"], 0)

        # Percentile should be between 0 and 100
        self.assertGreaterEqual(atr["percentile"], 0)
        self.assertLessEqual(atr["percentile"], 100)

    def test_volatility_trend(self):
        """Test volatility trend detection"""
        result = self.processor.process(self.increasing_volatility_data)

        self.assertIn("volatility_trend", result.data)
        vol_trend = result.data["volatility_trend"]

        self.assertIn("direction", vol_trend)
        self.assertIn("strength", vol_trend)
        self.assertIn("rate_of_change", vol_trend)

        # Increasing volatility should show upward trend
        self.assertEqual(vol_trend["direction"], "increasing")
        self.assertGreater(vol_trend["rate_of_change"], 0)

    def test_volatility_spike_detection(self):
        """Test detection of volatility spikes"""
        result = self.processor.process(self.spike_volatility_data)

        self.assertIn("volatility_events", result.data)
        events = result.data["volatility_events"]

        # Should detect spike events
        self.assertGreater(len(events), 0, "Should detect volatility spike events")

        if events:
            event = events[0]
            self.assertIn("type", event)
            self.assertIn("position", event)
            self.assertIn("magnitude", event)

    def test_historical_volatility(self):
        """Test historical volatility calculation"""
        result = self.processor.process(self.high_volatility_data)

        self.assertIn("historical_volatility", result.data)
        hist_vol = result.data["historical_volatility"]

        self.assertIn("hv_20", hist_vol)  # 20-period historical volatility
        self.assertIn("hv_50", hist_vol)  # 50-period historical volatility

        # Historical volatility should be positive
        for key, value in hist_vol.items():
            if value is not None:
                self.assertGreater(value, 0, f"{key} should be positive")

    def test_volatility_metrics(self):
        """Test volatility-related metrics"""
        result = self.processor.process(self.high_volatility_data)

        metrics = result.metrics

        self.assertIn("current_volatility", metrics)
        self.assertIn("average_volatility", metrics)
        self.assertIn("volatility_percentile", metrics)
        self.assertIn("volatility_zscore", metrics)

        # All metrics should be finite
        for key, value in metrics.items():
            self.assertTrue(np.isfinite(value), f"Metric {key} should be finite")

    def test_volatility_signals(self):
        """Test signal generation based on volatility"""
        # High volatility should generate warning signals
        high_vol_result = self.processor.process(self.high_volatility_data)
        high_vol_signals = high_vol_result.signals

        self.assertIsInstance(high_vol_signals, list)

        # Spike volatility should generate spike signals
        spike_result = self.processor.process(self.spike_volatility_data)
        spike_signals = spike_result.signals

        volatility_signal = any("volatility" in s.lower() for s in spike_signals)
        self.assertTrue(volatility_signal, "Should generate volatility-related signals")

    def test_volatility_regime(self):
        """Test volatility regime classification"""
        result = self.processor.process(self.low_volatility_data)

        self.assertIn("volatility_regime", result.data)
        regime = result.data["volatility_regime"]

        self.assertIn(regime, ["low", "normal", "high", "extreme"])

        # Low volatility data should be classified as low regime
        self.assertEqual(regime, "low")

        # High volatility should be classified differently
        high_result = self.processor.process(self.high_volatility_data)
        high_regime = high_result.data["volatility_regime"]
        self.assertIn(high_regime, ["high", "extreme"])

    def test_volatility_comparison(self):
        """Test volatility comparison with historical levels"""
        result = self.processor.process(self.high_volatility_data)

        self.assertIn("volatility_comparison", result.data)
        comparison = result.data["volatility_comparison"]

        self.assertIn("vs_average", comparison)
        self.assertIn("vs_median", comparison)
        self.assertIn("vs_recent", comparison)

        # Comparisons should be ratios (can be any positive value)
        for key, value in comparison.items():
            if value is not None:
                self.assertGreater(value, 0, f"{key} should be positive")

    def test_error_handling(self):
        """Test error handling with invalid data"""
        # Test with invalid data structure
        bad_data = [{"invalid": "data"}]
        result = self.processor.preprocess(bad_data)

        self.assertFalse(result.is_valid())
        self.assertGreater(len(result.errors), 0)

        # Test with insufficient data
        small_data = self.low_volatility_data[:3]
        result = self.processor.process(small_data)

        # Should still process but with limited analysis
        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid())

    def test_minimum_data_requirements(self):
        """Test processor with minimum required data"""
        # Test with minimum viable dataset
        min_data = self.low_volatility_data[:20]
        result = self.processor.process(min_data)

        self.assertIsNotNone(result)
        self.assertIn("current_volatility", result.data)
        self.assertIn("bollinger_bands", result.data)

        # Should still calculate basic metrics
        self.assertGreater(len(result.metrics), 0)


if __name__ == "__main__":
    unittest.main()
