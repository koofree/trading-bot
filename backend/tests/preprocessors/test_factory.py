"""
Test Suite for Preprocessor Factory and Orchestrator
Tests factory pattern, registry, and orchestration of multiple preprocessors
"""

import unittest
from typing import Dict, List

import numpy as np

from services.preprocessors import (
    CandlestickProcessor,
    TrendProcessor,
    VolumeProcessor,
)
from services.preprocessors.factory import (
    PreprocessorFactory,
    PreprocessorOrchestrator,
    PreprocessorRegistry,
    analyze_market_data,
    create_orchestrator,
)


class TestPreprocessorRegistry(unittest.TestCase):
    """Test preprocessor registry functionality"""

    def test_default_processors_registered(self):
        """Test that default processors are registered"""
        available = PreprocessorRegistry.list_available()

        expected = [
            "candlestick",
            "volume",
            "price_action",
            "trend",
            "volatility",
            "market_profile",
            "orderbook",
        ]

        for processor_name in expected:
            self.assertIn(processor_name, available)

    def test_get_processor_class(self):
        """Test retrieving processor classes from registry"""
        candlestick_class = PreprocessorRegistry.get("candlestick")
        self.assertEqual(candlestick_class, CandlestickProcessor)

        volume_class = PreprocessorRegistry.get("volume")
        self.assertEqual(volume_class, VolumeProcessor)

        # Test non-existent processor
        none_class = PreprocessorRegistry.get("non_existent")
        self.assertIsNone(none_class)

    def test_register_custom_processor(self):
        """Test registering a custom processor"""
        # Create a dummy processor class
        class CustomProcessor:
            pass

        # Register it
        PreprocessorRegistry.register("custom", CustomProcessor)

        # Verify it's registered
        self.assertIn("custom", PreprocessorRegistry.list_available())
        self.assertEqual(PreprocessorRegistry.get("custom"), CustomProcessor)


class TestPreprocessorFactory(unittest.TestCase):
    """Test preprocessor factory functionality"""

    def test_create_single_processor(self):
        """Test creating a single processor instance"""
        processor = PreprocessorFactory.create("candlestick")

        self.assertIsNotNone(processor)
        self.assertIsInstance(processor, CandlestickProcessor)
        self.assertEqual(processor.name, "candlestick")

    def test_create_with_config(self):
        """Test creating processor with configuration"""
        config = {"timeframe": "1h", "custom_param": 123}
        processor = PreprocessorFactory.create("volume", config)

        self.assertIsNotNone(processor)
        self.assertIsInstance(processor, VolumeProcessor)
        self.assertEqual(processor.config["timeframe"], "1h")
        self.assertEqual(processor.config["custom_param"], 123)

    def test_create_multiple_processors(self):
        """Test creating multiple processors at once"""
        names = ["candlestick", "volume", "trend"]
        processors = PreprocessorFactory.create_multiple(names)

        self.assertEqual(len(processors), 3)
        self.assertIn("candlestick", processors)
        self.assertIn("volume", processors)
        self.assertIn("trend", processors)

        self.assertIsInstance(processors["candlestick"], CandlestickProcessor)
        self.assertIsInstance(processors["volume"], VolumeProcessor)
        self.assertIsInstance(processors["trend"], TrendProcessor)

    def test_create_non_existent_processor(self):
        """Test creating a non-existent processor returns None"""
        processor = PreprocessorFactory.create("non_existent")
        self.assertIsNone(processor)

    def test_create_multiple_with_invalid(self):
        """Test creating multiple processors with some invalid names"""
        names = ["candlestick", "invalid_processor", "volume"]
        processors = PreprocessorFactory.create_multiple(names)

        # Should only create valid processors
        self.assertEqual(len(processors), 2)
        self.assertIn("candlestick", processors)
        self.assertIn("volume", processors)
        self.assertNotIn("invalid_processor", processors)


class TestPreprocessorOrchestrator(unittest.TestCase):
    """Test preprocessor orchestrator functionality"""

    def setUp(self):
        """Set up test data"""
        self.sample_data = self._generate_sample_data()
        self.orchestrator = PreprocessorOrchestrator()

    def _generate_sample_data(self) -> List[Dict]:
        """Generate sample market data"""
        data = []
        base_price = 100

        for i in range(50):
            price = base_price + np.random.randn() * 2
            data.append({
                "open": price,
                "high": price + abs(np.random.randn()),
                "low": price - abs(np.random.randn()),
                "close": price + np.random.randn() * 0.5,
                "volume": 1000 + np.random.randint(-100, 100)
            })
            base_price = price

        return data

    def test_orchestrator_initialization(self):
        """Test orchestrator initialization with default processors"""
        self.assertIsNotNone(self.orchestrator)
        self.assertEqual(len(self.orchestrator.processors), 5)  # Default 5 processors

        # Check default processors are loaded
        self.assertIn("candlestick", self.orchestrator.processors)
        self.assertIn("volume", self.orchestrator.processors)
        self.assertIn("price_action", self.orchestrator.processors)
        self.assertIn("trend", self.orchestrator.processors)
        self.assertIn("volatility", self.orchestrator.processors)

    def test_orchestrator_custom_processors(self):
        """Test orchestrator with custom processor list"""
        custom_orchestrator = PreprocessorOrchestrator(["candlestick", "volume"])

        self.assertEqual(len(custom_orchestrator.processors), 2)
        self.assertIn("candlestick", custom_orchestrator.processors)
        self.assertIn("volume", custom_orchestrator.processors)
        self.assertNotIn("trend", custom_orchestrator.processors)

    def test_process_all(self):
        """Test processing data through all orchestrator processors"""
        # Prepare data for each processor
        data = {
            "candlestick": self.sample_data,
            "volume": self.sample_data,
            "price_action": self.sample_data,
            "trend": self.sample_data,
            "volatility": self.sample_data,
        }

        results = self.orchestrator.process_all(data)

        self.assertEqual(len(results), 5)

        # Check each result
        for name, result in results.items():
            self.assertTrue(result.is_valid(), f"{name} should produce valid result")
            self.assertEqual(result.processor_name, name)

    def test_process_with_default_data(self):
        """Test processing with default data key"""
        data = {"default": self.sample_data}

        results = self.orchestrator.process_all(data)

        # All processors should use the default data
        self.assertEqual(len(results), 5)
        for result in results.values():
            self.assertTrue(result.is_valid())

    def test_get_combined_signals(self):
        """Test combining signals from multiple processors"""
        data = {"default": self.sample_data}
        results = self.orchestrator.process_all(data)

        combined_signals = self.orchestrator.get_combined_signals(results)

        self.assertIsInstance(combined_signals, list)

        # Signals should be prefixed with processor name
        for signal in combined_signals:
            self.assertTrue(signal.startswith("["), "Signal should be prefixed")
            self.assertIn("]", signal, "Signal should have closing bracket")

    def test_get_combined_metrics(self):
        """Test combining metrics from multiple processors"""
        data = {"default": self.sample_data}
        results = self.orchestrator.process_all(data)

        combined_metrics = self.orchestrator.get_combined_metrics(results)

        self.assertIsInstance(combined_metrics, dict)

        # Metrics should be prefixed with processor name
        for key in combined_metrics.keys():
            self.assertIn("_", key, "Metric key should contain underscore separator")

        # Should have metrics from multiple processors
        self.assertGreater(len(combined_metrics), 5)

    def test_generate_summary(self):
        """Test summary generation from orchestrator results"""
        data = {"default": self.sample_data}
        results = self.orchestrator.process_all(data)

        summary = self.orchestrator.generate_summary(results)

        self.assertIn("total_processors", summary)
        self.assertIn("successful", summary)
        self.assertIn("failed", summary)
        self.assertIn("signals", summary)
        self.assertIn("signal_count", summary)
        self.assertIn("key_metrics", summary)
        self.assertIn("dominant_pattern", summary)
        self.assertIn("overall_sentiment", summary)

        # Check counts
        self.assertEqual(summary["total_processors"], 5)
        self.assertEqual(summary["successful"], 5)
        self.assertEqual(summary["failed"], 0)

        # Sentiment should be one of the valid values
        self.assertIn(summary["overall_sentiment"], ["bullish", "bearish", "neutral"])

    def test_orchestrator_error_handling(self):
        """Test orchestrator handles processor errors gracefully"""
        # Provide invalid data for some processors
        data = {
            "candlestick": self.sample_data,
            "volume": [{"invalid": "data"}],  # Invalid data
            "price_action": self.sample_data,
            "trend": [],  # Empty data
            "volatility": self.sample_data,
        }

        results = self.orchestrator.process_all(data)

        # Should still get results for all processors
        self.assertEqual(len(results), 5)

        # Check which ones succeeded and failed
        self.assertTrue(results["candlestick"].is_valid())
        self.assertFalse(results["volume"].is_valid())
        self.assertTrue(results["price_action"].is_valid())
        self.assertFalse(results["trend"].is_valid())
        self.assertTrue(results["volatility"].is_valid())

        # Summary should reflect failures
        summary = self.orchestrator.generate_summary(results)
        self.assertEqual(summary["successful"], 3)
        self.assertEqual(summary["failed"], 2)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""

    def setUp(self):
        """Set up test data"""
        self.sample_candles = self._generate_sample_candles()

    def _generate_sample_candles(self) -> List[Dict]:
        """Generate sample candle data"""
        candles = []
        for i in range(50):
            price = 100 + np.random.randn() * 2
            candles.append({
                "open": price,
                "high": price + abs(np.random.randn()),
                "low": price - abs(np.random.randn()),
                "close": price + np.random.randn() * 0.5,
                "volume": 1000 + np.random.randint(-100, 100)
            })
        return candles

    def test_create_orchestrator_function(self):
        """Test create_orchestrator convenience function"""
        # Default orchestrator
        default_orch = create_orchestrator()
        self.assertIsInstance(default_orch, PreprocessorOrchestrator)
        self.assertEqual(len(default_orch.processors), 5)

        # Custom orchestrator
        custom_orch = create_orchestrator(["candlestick", "volume"])
        self.assertEqual(len(custom_orch.processors), 2)

    def test_analyze_market_data_function(self):
        """Test analyze_market_data convenience function"""
        analysis = analyze_market_data(self.sample_candles)

        self.assertIn("results", analysis)
        self.assertIn("summary", analysis)
        self.assertIn("signals", analysis)
        self.assertIn("metrics", analysis)

        # Check results structure
        self.assertIsInstance(analysis["results"], dict)
        self.assertIsInstance(analysis["summary"], dict)
        self.assertIsInstance(analysis["signals"], list)
        self.assertIsInstance(analysis["metrics"], dict)

        # Should have results for default processors
        self.assertIn("candlestick", analysis["results"])
        self.assertIn("volume", analysis["results"])

    def test_analyze_with_orderbook(self):
        """Test analyze_market_data with orderbook data"""
        orderbook = {
            "bids": [[100, 10], [99, 20], [98, 30]],
            "asks": [[101, 10], [102, 20], [103, 30]]
        }

        analysis = analyze_market_data(self.sample_candles, orderbook)

        # Should include orderbook analysis if processor is available
        # Note: orderbook processor might be a placeholder
        self.assertIsNotNone(analysis)
        self.assertIn("results", analysis)


if __name__ == "__main__":
    unittest.main()
