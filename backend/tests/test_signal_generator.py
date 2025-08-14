"""
Test Suite for Signal Generator
Tests the signal generator that uses preprocessors for analysis
"""

import unittest
from datetime import datetime
from unittest.mock import patch

import numpy as np
import pandas as pd

from services.signal_generator import SignalGenerator, SignalType, TradingSignal


class TestSignalGenerator(unittest.TestCase):
    """Test SignalGenerator functionality"""

    def setUp(self):
        """Set up test environment"""
        self.config = {
            "enabled_processors": [
                "candlestick",
                "volume",
                "price_action",
                "trend",
                "volatility",
            ],
            "signal_weights": {
                "candlestick": 0.15,
                "volume": 0.15,
                "price_action": 0.25,
                "trend": 0.25,
                "volatility": 0.10,
                "llm": 0.10,
            },
            "min_confidence": 0.6,
            "strong_signal_threshold": 0.8,
            "base_position_size": 0.02,
            "max_position_size": 0.1,
        }

        self.generator = SignalGenerator(self.config)

        # Create sample market data
        self.market_data = self._create_sample_market_data()

    def _create_sample_market_data(self) -> pd.DataFrame:
        """Create sample OHLCV market data"""
        dates = pd.date_range(start="2024-01-01", periods=100, freq="h")

        # Generate trending price data
        np.random.seed(42)
        base_price = 100
        prices = []

        for i in range(100):
            trend = i * 0.5  # Upward trend
            noise = np.random.randn() * 2
            price = base_price + trend + noise
            prices.append(price)

        data = {
            "timestamp": dates,
            "open": prices,
            "high": [p + np.random.uniform(0, 2) for p in prices],
            "low": [p - np.random.uniform(0, 2) for p in prices],
            "close": [p + np.random.uniform(-1, 1) for p in prices],
            "volume": [1000 + np.random.randint(-100, 100) for _ in range(100)],
            "market": ["BTC-USD"] * 100,
        }

        return pd.DataFrame(data)

    def test_initialization(self):
        """Test SignalGenerator initialization"""
        self.assertIsNotNone(self.generator.orchestrator)
        self.assertEqual(
            self.generator.enabled_processors, self.config["enabled_processors"]
        )
        self.assertEqual(self.generator.signal_weights, self.config["signal_weights"])
        self.assertEqual(self.generator.min_confidence, self.config["min_confidence"])

    @patch("services.signal_generator.analyze_market_data")
    def test_generate_signal_basic(self, mock_analyze):
        """Test basic signal generation"""
        # Mock preprocessor results
        mock_results = self._create_mock_preprocessor_results()
        mock_analyze.return_value = mock_results

        # Generate signal
        signal = self.generator.generate_signal(self.market_data)

        # Verify signal structure
        self.assertIsInstance(signal, TradingSignal)
        self.assertIn(
            signal.signal_type, [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
        )
        self.assertIsInstance(signal.strength, float)
        self.assertGreaterEqual(signal.strength, 0)
        self.assertLessEqual(signal.strength, 1)
        self.assertIsInstance(signal.price, float)
        self.assertIsInstance(signal.volume, float)
        self.assertIsInstance(signal.preprocessor_analysis, dict)
        self.assertIsInstance(signal.llm_context, str)
        self.assertIsInstance(signal.reasoning, str)
        self.assertIsInstance(signal.timestamp, datetime)

    def _create_mock_preprocessor_results(self) -> dict:
        """Create mock preprocessor results"""

        class MockResult:
            def __init__(self, processor_name, valid=True):
                self.processor_name = processor_name
                self.valid = valid
                self.signals = []
                self.metrics = {}
                self.data = {}

            def is_valid(self):
                return self.valid

        # Create bullish scenario results
        results = {}

        # Candlestick processor
        candle_result = MockResult("candlestick")
        candle_result.signals = ["Bullish hammer pattern detected"]
        candle_result.data = {
            "current_candle": {"type": "hammer", "bullish": True},
            "patterns": ["hammer", "doji"],
            "candle_strength": {"bullish_ratio": 0.7, "bearish_ratio": 0.3},
        }
        candle_result.metrics = {"pattern_count": 2}
        results["candlestick"] = candle_result

        # Volume processor
        volume_result = MockResult("volume")
        volume_result.signals = ["Volume accumulation phase"]
        volume_result.data = {
            "indicators": {"obv_trend": "rising", "mfi": 65},
            "patterns": {"phase": "accumulation", "volume_trend": "increasing"},
        }
        volume_result.metrics = {"volume_ratio": 1.5}
        results["volume"] = volume_result

        # Price action processor
        price_result = MockResult("price_action")
        price_result.signals = ["Resistance breakout detected"]
        price_result.data = {
            "breakouts": {"resistance_break": True, "support_break": False},
            "key_levels": {"strong_support": 95, "strong_resistance": 105},
            "market_structure": {"trend": "bullish"},
        }
        price_result.metrics = {"price_momentum": 0.8}
        results["price_action"] = price_result

        # Trend processor
        trend_result = MockResult("trend")
        trend_result.signals = ["Strong uptrend confirmed"]
        trend_result.data = {
            "trend_direction": "uptrend",
            "trend_strength": 75,
            "ma_crossovers": {"golden_cross": True, "death_cross": False},
            "trend_channel": {"upper_channel": 110, "lower_channel": 90},
        }
        trend_result.metrics = {"trend_score": 80}
        results["trend"] = trend_result

        # Volatility processor
        vol_result = MockResult("volatility")
        vol_result.signals = ["Normal volatility regime"]
        vol_result.data = {
            "volatility_regime": "normal",
            "current_volatility": 15.5,
            "bollinger_bands": {"upper": 105, "middle": 100, "lower": 95},
            "atr": {"value": 2.5},
        }
        vol_result.metrics = {"volatility_percentile": 50}
        results["volatility"] = vol_result

        return results

    @patch("services.signal_generator.analyze_market_data")
    def test_bullish_signal_generation(self, mock_analyze):
        """Test generation of bullish signal"""
        # Create strongly bullish results
        mock_results = self._create_mock_preprocessor_results()
        mock_analyze.return_value = mock_results

        signal = self.generator.generate_signal(self.market_data)

        # Should generate BUY signal
        self.assertEqual(signal.signal_type, SignalType.BUY)
        self.assertGreater(signal.strength, 0.6)
        self.assertIn("uptrend", signal.reasoning.lower())

    @patch("services.signal_generator.analyze_market_data")
    def test_bearish_signal_generation(self, mock_analyze):
        """Test generation of bearish signal"""
        # Create bearish scenario
        mock_results = self._create_bearish_preprocessor_results()
        mock_analyze.return_value = mock_results

        signal = self.generator.generate_signal(self.market_data)

        # Should generate SELL signal
        self.assertEqual(signal.signal_type, SignalType.SELL)
        self.assertGreater(signal.strength, 0.6)
        self.assertIn("downtrend", signal.reasoning.lower())

    def _create_bearish_preprocessor_results(self) -> dict:
        """Create mock bearish preprocessor results"""

        class MockResult:
            def __init__(self, processor_name, valid=True):
                self.processor_name = processor_name
                self.valid = valid
                self.signals = []
                self.metrics = {}
                self.data = {}

            def is_valid(self):
                return self.valid

        results = {}

        # Bearish candlestick
        candle_result = MockResult("candlestick")
        candle_result.signals = ["Bearish engulfing pattern"]
        candle_result.data = {
            "current_candle": {"type": "engulfing", "bearish": True},
            "patterns": ["bearish_engulfing"],
            "candle_strength": {"bullish_ratio": 0.2, "bearish_ratio": 0.8},
        }
        results["candlestick"] = candle_result

        # Distribution volume
        volume_result = MockResult("volume")
        volume_result.signals = ["Volume distribution phase"]
        volume_result.data = {
            "indicators": {"obv_trend": "falling", "mfi": 30},
            "patterns": {"phase": "distribution", "volume_trend": "decreasing"},
        }
        results["volume"] = volume_result

        # Support breakdown
        price_result = MockResult("price_action")
        price_result.signals = ["Support breakdown detected"]
        price_result.data = {
            "breakouts": {"resistance_break": False, "support_break": True},
            "key_levels": {"strong_support": 95, "strong_resistance": 105},
        }
        results["price_action"] = price_result

        # Downtrend
        trend_result = MockResult("trend")
        trend_result.signals = ["Strong downtrend confirmed"]
        trend_result.data = {
            "trend_direction": "downtrend",
            "trend_strength": -70,
            "ma_crossovers": {"golden_cross": False, "death_cross": True},
        }
        results["trend"] = trend_result

        # High volatility
        vol_result = MockResult("volatility")
        vol_result.signals = ["High volatility detected"]
        vol_result.data = {"volatility_regime": "high", "current_volatility": 35}
        results["volatility"] = vol_result

        return results

    @patch("services.signal_generator.analyze_market_data")
    def test_hold_signal_generation(self, mock_analyze):
        """Test generation of HOLD signal in neutral conditions"""
        # Create neutral/mixed results
        mock_results = self._create_neutral_preprocessor_results()
        mock_analyze.return_value = mock_results

        signal = self.generator.generate_signal(self.market_data)

        # Should generate HOLD signal
        self.assertEqual(signal.signal_type, SignalType.HOLD)

    def _create_neutral_preprocessor_results(self) -> dict:
        """Create mock neutral preprocessor results"""

        class MockResult:
            def __init__(self, processor_name):
                self.processor_name = processor_name
                self.signals = []
                self.metrics = {}
                self.data = {}

            def is_valid(self):
                return True

        results = {}

        # Mixed signals
        for proc in ["candlestick", "volume", "price_action", "trend", "volatility"]:
            result = MockResult(proc)
            result.signals = ["Neutral market conditions"]
            result.data = {"trend_direction": "sideways"}
            results[proc] = result

        return results

    def test_llm_context_formatting(self):
        """Test LLM context string formatting"""
        analysis = {
            "indicators": {
                "trend": {"direction": "uptrend", "strength": 75},
                "volume": {
                    "obv_trend": "rising",
                    "volume_phase": "accumulation",
                    "mfi": 65,
                },
            },
            "market_conditions": {
                "volatility": {"regime": "normal", "current_volatility": 15.5}
            },
            "patterns": {
                "candlestick": {"patterns_found": ["hammer", "doji"]},
                "price_action": {"breakouts": {"resistance_break": True}},
            },
            "signals": [
                {"processor": "trend", "signal": "Strong uptrend"},
                {"processor": "volume", "signal": "Accumulation phase"},
            ],
        }

        llm_context = self.generator._format_for_llm(analysis, self.market_data)

        # Check context contains key information
        self.assertIn("Market Analysis Summary", llm_context)
        self.assertIn("Current Market State", llm_context)
        self.assertIn("Technical Indicators", llm_context)
        self.assertIn("Trend", llm_context)
        self.assertIn("uptrend", llm_context.lower())
        self.assertIn("Volume", llm_context)
        self.assertIn("Volatility", llm_context)
        self.assertIn("Trading Signals", llm_context)
        self.assertIn("Analysis Request", llm_context)

    def test_signal_score_calculation(self):
        """Test signal score calculation logic"""
        analysis = {
            "signals": [
                {"processor": "trend", "signal": "Strong bullish uptrend"},
                {"processor": "volume", "signal": "Accumulation phase detected"},
                {"processor": "candlestick", "signal": "Bearish pattern"},
            ],
            "indicators": {
                "trend": {"direction": "uptrend", "strength": 80},
                "volume": {"volume_phase": "accumulation"},
            },
            "patterns": {"price_action": {"breakouts": {"resistance_break": True}}},
            "market_conditions": {"volatility": {"regime": "normal"}},
        }

        buy_score, sell_score, reasons = self.generator._calculate_signal_scores(
            analysis
        )

        # Buy score should be higher due to bullish signals
        self.assertGreater(buy_score, sell_score)
        self.assertIsInstance(reasons, list)
        self.assertGreater(len(reasons), 0)

    def test_position_size_calculation(self):
        """Test position size calculation based on signal strength"""
        # Test with different signal strengths
        test_cases = [
            (0.5, 100, 0.015),  # 50% strength -> 1.5% position
            (1.0, 100, 0.02),  # 100% strength -> 2% position
            (0.8, 100, 0.018),  # 80% strength -> 1.8% position
        ]

        for strength, price, expected_min in test_cases:
            position_size = self.generator._calculate_position_size(strength, price)
            self.assertGreaterEqual(position_size, expected_min)
            self.assertLessEqual(position_size, self.config["max_position_size"])

    def test_signal_to_dict(self):
        """Test TradingSignal.to_dict() method"""
        signal = TradingSignal(
            market="BTC-USD",
            signal_type=SignalType.BUY,
            strength=0.75,
            price=100.50,
            volume=0.02,
            preprocessor_analysis={"test": "data"},
            llm_context="Test context",
            reasoning="Test reasoning",
            timestamp=datetime.now(),
        )

        signal_dict = signal.to_dict()

        self.assertEqual(signal_dict["market"], "BTC-USD")
        self.assertEqual(signal_dict["signal_type"], "BUY")
        self.assertEqual(signal_dict["strength"], 0.75)
        self.assertEqual(signal_dict["price"], 100.50)
        self.assertEqual(signal_dict["volume"], 0.02)
        self.assertEqual(signal_dict["preprocessor_analysis"], {"test": "data"})
        self.assertEqual(signal_dict["llm_context"], "Test context")
        self.assertEqual(signal_dict["reasoning"], "Test reasoning")
        self.assertIn("timestamp", signal_dict)

    @patch("services.signal_generator.analyze_market_data")
    def test_export_llm_training_data(self, mock_analyze):
        """Test export of LLM training data"""
        mock_results = self._create_mock_preprocessor_results()
        mock_analyze.return_value = mock_results

        # Generate signal
        signal = self.generator.generate_signal(self.market_data)

        # Export training data
        training_data = self.generator.export_llm_training_data(
            self.market_data, signal, actual_outcome={"profit": 5.2, "success": True}
        )

        # Verify training data structure
        self.assertIn("timestamp", training_data)
        self.assertIn("market", training_data)
        self.assertIn("input", training_data)
        self.assertIn("output", training_data)
        self.assertIn("labels", training_data)
        self.assertIn("metadata", training_data)

        # Check input structure
        self.assertIn("llm_context", training_data["input"])
        self.assertIn("preprocessor_analysis", training_data["input"])
        self.assertIn("market_snapshot", training_data["input"])

        # Check output structure
        self.assertIn("signal_type", training_data["output"])
        self.assertIn("strength", training_data["output"])
        self.assertIn("reasoning", training_data["output"])
        self.assertIn("position_size", training_data["output"])

        # Check metadata
        self.assertEqual(training_data["metadata"]["generator_version"], "v2")
        self.assertEqual(
            training_data["metadata"]["enabled_processors"],
            self.config["enabled_processors"],
        )

    @patch("services.signal_generator.analyze_market_data")
    def test_with_llm_analysis(self, mock_analyze):
        """Test signal generation with LLM analysis input"""
        mock_results = self._create_mock_preprocessor_results()
        mock_analyze.return_value = mock_results

        # Add LLM analysis
        llm_analysis = {
            "sentiment_score": 0.7,
            "market_outlook": "bullish",
            "key_insights": ["Strong momentum", "Breaking resistance"],
        }

        signal = self.generator.generate_signal(
            self.market_data, llm_analysis=llm_analysis
        )

        # Should incorporate LLM sentiment
        self.assertEqual(signal.signal_type, SignalType.BUY)
        # Check that LLM sentiment is included in reasoning (could be "Positive LLM sentiment")
        self.assertTrue(
            "llm sentiment" in signal.reasoning.lower()
            or "sentiment" in signal.reasoning.lower(),
            f"Expected 'sentiment' in reasoning but got: {signal.reasoning}",
        )

    @patch("services.signal_generator.analyze_market_data")
    def test_high_volatility_adjustment(self, mock_analyze):
        """Test signal adjustment in high volatility"""
        mock_results = self._create_mock_preprocessor_results()

        # Set high volatility
        mock_results["volatility"].data["volatility_regime"] = "extreme"
        mock_analyze.return_value = mock_results

        signal = self.generator.generate_signal(self.market_data)

        # Signal should mention volatility adjustment
        self.assertIn("volatility", signal.reasoning.lower())

    def test_error_handling_empty_data(self):
        """Test error handling with empty market data"""
        empty_df = pd.DataFrame()

        # Should handle gracefully without crashing
        with self.assertRaises(Exception):
            self.generator.generate_signal(empty_df)

    @patch("services.signal_generator.analyze_market_data")
    def test_invalid_preprocessor_results(self, mock_analyze):
        """Test handling of invalid preprocessor results"""

        class MockResult:
            def __init__(self, valid=False):
                self.valid = valid
                self.signals = []
                self.metrics = {}
                self.data = {}

            def is_valid(self):
                return self.valid

        # All processors return invalid results
        mock_results = {
            proc: MockResult(valid=False)
            for proc in ["candlestick", "volume", "price_action", "trend", "volatility"]
        }
        mock_analyze.return_value = mock_results

        signal = self.generator.generate_signal(self.market_data)

        # Should still generate a signal (likely HOLD)
        self.assertIsInstance(signal, TradingSignal)
        self.assertEqual(signal.signal_type, SignalType.HOLD)


if __name__ == "__main__":
    unittest.main()
