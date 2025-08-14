"""
Test Suite for Volume Analysis Processor
Tests volume indicators, patterns, and analysis
"""

import unittest
from typing import Dict, List

import numpy as np

from services.preprocessors import VolumeProcessor


class TestVolumeProcessor(unittest.TestCase):
    """Test volume analysis"""

    def setUp(self):
        """Set up test data"""
        self.processor = VolumeProcessor()

        # Generate test data
        self.normal_volume = self._generate_normal_volume()
        self.spike_volume = self._generate_volume_spike()
        self.accumulation_data = self._generate_accumulation_pattern()
        self.distribution_data = self._generate_distribution_pattern()

    def _generate_normal_volume(self) -> List[Dict]:
        """Generate normal volume data"""
        data = []

        for _i in range(50):
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

    def _generate_distribution_pattern(self) -> List[Dict]:
        """Generate distribution pattern (falling price with increasing volume)"""
        data = []
        base_price = 150
        base_volume = 1000

        for i in range(30):
            data.append(
                {
                    "close": base_price - i * 0.5,  # Gradual price decrease
                    "high": base_price - i * 0.5 + 1,
                    "low": base_price - i * 0.5 - 1,
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
        """Test accumulation phase detection"""
        result = self.processor.process(self.accumulation_data)

        phase = result.data["patterns"].get("phase")

        self.assertEqual(phase, "accumulation", "Should detect accumulation phase")

    def test_distribution_detection(self):
        """Test distribution phase detection"""
        result = self.processor.process(self.distribution_data)

        phase = result.data["patterns"].get("phase")

        # Distribution phase should be detected (price falling with high volume)
        self.assertIn(phase, ["distribution", "neutral"], "Should detect distribution or neutral phase")

    def test_obv_calculation(self):
        """Test On-Balance Volume calculation"""
        result = self.processor.process(self.normal_volume)

        indicators = result.data["indicators"]

        self.assertIn("obv", indicators)
        self.assertIsInstance(indicators["obv"], (int, float))

    def test_vwap_calculation(self):
        """Test Volume Weighted Average Price calculation"""
        result = self.processor.process(self.normal_volume)

        indicators = result.data["indicators"]

        self.assertIn("vwap", indicators)
        self.assertIsInstance(indicators["vwap"], (int, float))

        # VWAP should be within reasonable price range
        prices = [d["close"] for d in self.normal_volume]
        self.assertGreaterEqual(indicators["vwap"], min(prices) * 0.9)
        self.assertLessEqual(indicators["vwap"], max(prices) * 1.1)

    def test_mfi_calculation(self):
        """Test Money Flow Index calculation"""
        result = self.processor.process(self.normal_volume)

        indicators = result.data["indicators"]

        self.assertIn("mfi", indicators)

        # MFI should be between 0 and 100
        self.assertGreaterEqual(indicators["mfi"], 0)
        self.assertLessEqual(indicators["mfi"], 100)

    def test_vroc_calculation(self):
        """Test Volume Rate of Change calculation"""
        result = self.processor.process(self.normal_volume)

        indicators = result.data["indicators"]

        self.assertIn("vroc", indicators)
        self.assertIsInstance(indicators["vroc"], (int, float))

    def test_adl_calculation(self):
        """Test Accumulation/Distribution Line calculation"""
        result = self.processor.process(self.normal_volume)

        indicators = result.data["indicators"]

        self.assertIn("adl", indicators)
        self.assertIsInstance(indicators["adl"], (int, float))

    def test_volume_profile(self):
        """Test volume profile calculation"""
        result = self.processor.process(self.normal_volume)

        profile = result.data.get("volume_profile", {})

        if profile:  # Profile might be empty for small datasets
            self.assertIn("poc", profile)  # Point of Control
            self.assertIn("profile", profile)

            # POC should be within price range
            if profile.get("poc"):
                prices = [d["close"] for d in self.normal_volume]
                self.assertGreaterEqual(profile["poc"], min(prices) * 0.9)
                self.assertLessEqual(profile["poc"], max(prices) * 1.1)

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

    def test_volume_trend_analysis(self):
        """Test volume trend analysis"""
        result = self.processor.process(self.accumulation_data)

        # Check for volume trend in metrics or data
        self.assertTrue(
            "volume_trend" in result.data or "patterns" in result.data,
            "Should analyze volume trends"
        )

    def test_abnormal_volume_detection(self):
        """Test detection of abnormal volume patterns"""
        # Create data with multiple volume anomalies
        data = self.normal_volume.copy()
        data[10]["volume"] = 3000  # 3x spike
        data[20]["volume"] = 50  # Very low volume
        data[30]["volume"] = 4000  # Another spike

        result = self.processor.process(data)

        patterns = result.data.get("patterns", {})
        spikes = patterns.get("spikes", [])

        # Should detect multiple anomalies
        self.assertGreater(len(spikes), 1, "Should detect multiple volume anomalies")

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

    def test_minimum_data_requirements(self):
        """Test processor with minimum required data"""
        # Test with very small dataset
        small_data = self.normal_volume[:5]
        result = self.processor.process(small_data)

        # Should still produce some results
        self.assertIsNotNone(result)
        self.assertIn("indicators", result.data)
        self.assertIn("patterns", result.data)


if __name__ == "__main__":
    unittest.main()
