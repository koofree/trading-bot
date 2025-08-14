"""
Test Suite for Market Data Preprocessors
Tests each preprocessor module individually and in combination
"""

import unittest
from typing import Dict, List

import numpy as np

# Import preprocessors
from services.preprocessors import (
    CandlestickProcessor,
    VolumeProcessor,
)


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
        for i in range(5):
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


class TestVolumeProcessor(unittest.TestCase):
    """Test volume analysis"""

    def setUp(self):
        """Set up test data"""
        self.processor = VolumeProcessor()

        # Generate test data
        self.normal_volume = self._generate_normal_volume()
        self.spike_volume = self._generate_volume_spike()
        self.accumulation_data = self._generate_accumulation_pattern()

    def _generate_normal_volume(self) -> List[Dict]:
        """Generate normal volume data"""
        data = []

        for i in range(50):
            data.append(
                {
                    "close": 100 + np.random.randn() * 2,
                    "high": 102 + np.random.randn(),
                    "low": 98 + np.random.randn(),
                    "volume": 1000 + np.random.randint(-100, 100),
                }
            )

        return data

    def _generate_volume_spike(self) -> List[Dict]:
        """Generate data with volume spike"""
        data = self._generate_normal_volume()

        # Add volume spike
        data[-1]["volume"] = 5000  # 5x normal volume
        data[-1]["close"] = data[-2]["close"] * 1.05  # Price increase

        return data

    def _generate_accumulation_pattern(self) -> List[Dict]:
        """Generate accumulation pattern (rising price with increasing volume)"""
        data = []
        base_price = 100
        base_volume = 1000

        for i in range(30):
            data.append(
                {
                    "close": base_price + i * 0.5,  # Gradual price increase
                    "high": base_price + i * 0.5 + 1,
                    "low": base_price + i * 0.5 - 1,
                    "volume": base_volume + i * 50,  # Increasing volume
                }
            )

        return data

    def test_validate_input(self):
        """Test input validation"""
        self.assertTrue(self.processor.validate_input(self.normal_volume))
        self.assertFalse(self.processor.validate_input([]))
        self.assertFalse(
            self.processor.validate_input([{"close": 100}])
        )  # Missing volume

    def test_volume_metrics(self):
        """Test volume metrics calculation"""
        result = self.processor.process(self.normal_volume)

        metrics = result.metrics

        self.assertIn("current_volume", metrics)
        self.assertIn("average_volume", metrics)
        self.assertIn("volume_ratio", metrics)
        self.assertIn("volume_zscore", metrics)

        # Volume ratio should be reasonable
        self.assertGreater(metrics["volume_ratio"], 0)
        self.assertLess(metrics["volume_ratio"], 10)

    def test_volume_spike_detection(self):
        """Test volume spike detection"""
        result = self.processor.process(self.spike_volume)

        patterns = result.data["patterns"]
        spikes = patterns.get("spikes", [])

        self.assertGreater(len(spikes), 0, "Volume spike should be detected")

        # Check last spike
        if spikes:
            last_spike = spikes[-1]
            self.assertGreater(last_spike["ratio"], 3, "Spike should be significant")

    def test_accumulation_detection(self):
        """Test accumulation/distribution phase detection"""
        result = self.processor.process(self.accumulation_data)

        phase = result.data["patterns"].get("phase")

        self.assertEqual(phase, "accumulation", "Should detect accumulation phase")

    def test_volume_indicators(self):
        """Test volume indicator calculations"""
        result = self.processor.process(self.normal_volume)

        indicators = result.data["indicators"]

        self.assertIn("obv", indicators)
        self.assertIn("vwap", indicators)
        self.assertIn("mfi", indicators)
        self.assertIn("vroc", indicators)
        self.assertIn("adl", indicators)

        # MFI should be between 0 and 100
        self.assertGreaterEqual(indicators["mfi"], 0)
        self.assertLessEqual(indicators["mfi"], 100)

    def test_volume_profile(self):
        """Test volume profile calculation"""
        result = self.processor.process(self.normal_volume)

        profile = result.data.get("volume_profile", {})

        if profile:  # Profile might be empty for small datasets
            self.assertIn("poc", profile)  # Point of Control
            self.assertIn("profile", profile)

    def test_price_volume_correlation(self):
        """Test price-volume correlation calculation"""
        result = self.processor.process(self.normal_volume)

        correlation = result.data.get("price_volume_correlation", 0)

        # Correlation should be between -1 and 1
        self.assertGreaterEqual(correlation, -1)
        self.assertLessEqual(correlation, 1)

    def test_volume_signals(self):
        """Test signal generation"""
        result = self.processor.process(self.spike_volume)

        signals = result.signals

        self.assertIsInstance(signals, list)

        # Should have some signal for the spike
        spike_signal_found = any("spike" in s.lower() for s in signals)
        self.assertTrue(spike_signal_found, "Should generate signal for volume spike")


class TestPreprocessorIntegration(unittest.TestCase):
    """Test multiple preprocessors working together"""

    def setUp(self):
        """Set up test data and processors"""
        self.candle_processor = CandlestickProcessor()
        self.volume_processor = VolumeProcessor()

        # Generate comprehensive test data
        self.market_data = self._generate_market_data()

    def _generate_market_data(self) -> List[Dict]:
        """Generate comprehensive market data"""
        data = []
        base_price = 100

        for i in range(100):
            # Simulate market movement
            trend = np.sin(i * 0.1) * 5  # Sinusoidal trend
            noise = np.random.randn() * 2

            open_price = base_price + trend + noise
            close_price = open_price + np.random.randn() * 2

            data.append(
                {
                    "open": open_price,
                    "high": max(open_price, close_price) + abs(np.random.randn()),
                    "low": min(open_price, close_price) - abs(np.random.randn()),
                    "close": close_price,
                    "volume": 1000 + abs(np.random.randn() * 200),
                }
            )

            base_price = close_price

        return data

    def test_combined_analysis(self):
        """Test combining results from multiple processors"""
        # Process with both processors
        candle_result = self.candle_processor.process(self.market_data)
        volume_result = self.volume_processor.process(self.market_data)

        # Both should succeed
        self.assertTrue(candle_result.is_valid())
        self.assertTrue(volume_result.is_valid())

        # Combine insights
        combined_signals = candle_result.signals + volume_result.signals

        self.assertIsInstance(combined_signals, list)

        # Check for comprehensive analysis
        self.assertIn("patterns", candle_result.data)
        self.assertIn("indicators", volume_result.data)

    def test_data_consistency(self):
        """Test that processors handle the same data consistently"""
        # Process same data multiple times
        result1 = self.candle_processor.process(self.market_data)
        result2 = self.candle_processor.process(self.market_data)

        # Results should be identical
        self.assertEqual(
            result1.data["support_resistance"]["support"],
            result2.data["support_resistance"]["support"],
        )

    def test_error_handling(self):
        """Test error handling across processors"""
        bad_data = [{"invalid": "data"}]

        candle_result = self.candle_processor.preprocess(bad_data)
        volume_result = self.volume_processor.preprocess(bad_data)

        # Both should handle errors gracefully
        self.assertFalse(candle_result.is_valid())
        self.assertFalse(volume_result.is_valid())
        self.assertGreater(len(candle_result.errors), 0)
        self.assertGreater(len(volume_result.errors), 0)


def run_tests():
    """Run all preprocessor tests"""
    # Create test suite
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTest(unittest.makeSuite(TestCandlestickProcessor))
    suite.addTest(unittest.makeSuite(TestVolumeProcessor))
    suite.addTest(unittest.makeSuite(TestPreprocessorIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    # Run tests
    test_result = run_tests()

    # Print summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Tests run: {test_result.testsRun}")
    print(f"Failures: {len(test_result.failures)}")
    print(f"Errors: {len(test_result.errors)}")

    if test_result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")

        if test_result.failures:
            print("\nFailures:")
            for test, traceback in test_result.failures:
                print(f"  - {test}: {traceback.split(chr(10))[0]}")

        if test_result.errors:
            print("\nErrors:")
            for test, traceback in test_result.errors:
                print(f"  - {test}: {traceback.split(chr(10))[0]}")
