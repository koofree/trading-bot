"""
Preprocessor Factory and Registry
Manages creation and orchestration of market data preprocessors
"""

from typing import Dict, List, Optional, Type

from .base import BasePreprocessor, PreprocessorResult
from .candlestick import CandlestickProcessor
from .market_profile import MarketProfileProcessor
from .orderbook import OrderbookProcessor
from .price_action import PriceActionProcessor
from .trend import TrendProcessor
from .volatility import VolatilityProcessor
from .volume import VolumeProcessor


class PreprocessorRegistry:
    """Registry of available preprocessors"""

    _processors: Dict[str, Type[BasePreprocessor]] = {
        "candlestick": CandlestickProcessor,
        "volume": VolumeProcessor,
        "price_action": PriceActionProcessor,
        "trend": TrendProcessor,
        "volatility": VolatilityProcessor,
        "market_profile": MarketProfileProcessor,
        "orderbook": OrderbookProcessor,
    }

    @classmethod
    def register(cls, name: str, processor_class: Type[BasePreprocessor]):
        """Register a new preprocessor"""
        cls._processors[name] = processor_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[BasePreprocessor]]:
        """Get a preprocessor class by name"""
        return cls._processors.get(name)

    @classmethod
    def list_available(cls) -> List[str]:
        """List all available preprocessor names"""
        return list(cls._processors.keys())


class PreprocessorFactory:
    """Factory for creating preprocessor instances"""

    @staticmethod
    def create(name: str, config: Optional[Dict] = None) -> Optional[BasePreprocessor]:
        """
        Create a preprocessor instance

        Args:
            name: Name of the preprocessor
            config: Optional configuration dictionary

        Returns:
            Preprocessor instance or None if not found
        """
        processor_class = PreprocessorRegistry.get(name)

        if processor_class:
            return processor_class(config)

        return None

    @staticmethod
    def create_multiple(
        names: List[str], config: Optional[Dict] = None
    ) -> Dict[str, BasePreprocessor]:
        """
        Create multiple preprocessor instances

        Args:
            names: List of preprocessor names
            config: Optional configuration dictionary (applied to all)

        Returns:
            Dictionary of preprocessor instances
        """
        processors = {}

        for name in names:
            processor = PreprocessorFactory.create(name, config)
            if processor:
                processors[name] = processor

        return processors


class PreprocessorOrchestrator:
    """Orchestrates multiple preprocessors for comprehensive analysis"""

    def __init__(self, preprocessor_names: Optional[List[str]] = None):
        """
        Initialize orchestrator with specified preprocessors

        Args:
            preprocessor_names: List of preprocessor names to use
                               If None, uses default set
        """
        if preprocessor_names is None:
            preprocessor_names = [
                "candlestick",
                "volume",
                "price_action",
                "trend",
                "volatility",
            ]

        self.processors = PreprocessorFactory.create_multiple(preprocessor_names)

    def process_all(self, data: Dict[str, any]) -> Dict[str, PreprocessorResult]:
        """
        Process data through all configured preprocessors

        Args:
            data: Dictionary with data for each processor
                  Keys should match processor names

        Returns:
            Dictionary of results from each processor
        """
        results = {}

        for name, processor in self.processors.items():
            # Get data for this processor
            processor_data = data.get(name, data.get("default"))

            if processor_data is not None:
                result = processor.preprocess(processor_data)
                results[name] = result

        return results

    def get_combined_signals(self, results: Dict[str, PreprocessorResult]) -> List[str]:
        """
        Combine signals from all processor results

        Args:
            results: Dictionary of processor results

        Returns:
            Combined list of unique signals
        """
        all_signals = []

        for name, result in results.items():
            if result.is_valid():
                # Add processor name to signals for context
                for signal in result.signals:
                    all_signals.append(f"[{name}] {signal}")

        # Remove duplicates while preserving order
        seen = set()
        unique_signals = []
        for signal in all_signals:
            if signal not in seen:
                seen.add(signal)
                unique_signals.append(signal)

        return unique_signals

    def get_combined_metrics(
        self, results: Dict[str, PreprocessorResult]
    ) -> Dict[str, float]:
        """
        Combine metrics from all processor results

        Args:
            results: Dictionary of processor results

        Returns:
            Combined dictionary of metrics with prefixed keys
        """
        combined = {}

        for name, result in results.items():
            if result.is_valid():
                for metric_key, metric_value in result.metrics.items():
                    combined[f"{name}_{metric_key}"] = metric_value

        return combined

    def generate_summary(self, results: Dict[str, PreprocessorResult]) -> Dict:
        """
        Generate a summary of all processor results

        Args:
            results: Dictionary of processor results

        Returns:
            Summary dictionary with key insights
        """
        summary = {
            "total_processors": len(results),
            "successful": sum(1 for r in results.values() if r.is_valid()),
            "failed": sum(1 for r in results.values() if not r.is_valid()),
            "signals": self.get_combined_signals(results),
            "signal_count": len(self.get_combined_signals(results)),
            "key_metrics": {},
            "dominant_pattern": None,
            "overall_sentiment": "neutral",
        }

        # Extract key metrics
        metrics = self.get_combined_metrics(results)

        # Determine overall sentiment based on signals
        bullish_count = sum(
            1
            for s in summary["signals"]
            if "bullish" in s.lower() or "buy" in s.lower()
        )
        bearish_count = sum(
            1
            for s in summary["signals"]
            if "bearish" in s.lower() or "sell" in s.lower()
        )

        if bullish_count > bearish_count * 1.5:
            summary["overall_sentiment"] = "bullish"
        elif bearish_count > bullish_count * 1.5:
            summary["overall_sentiment"] = "bearish"

        # Extract key patterns
        if "candlestick" in results and results["candlestick"].is_valid():
            patterns = results["candlestick"].data.get("patterns", [])
            if patterns:
                summary["dominant_pattern"] = patterns[0].get("name")

        # Add most important metrics
        important_metrics = [
            "volume_volume_ratio",
            "trend_trend_score",
            "volatility_current_volatility",
            "candlestick_body_ratio",
        ]

        for metric in important_metrics:
            if metric in metrics:
                summary["key_metrics"][metric] = metrics[metric]

        return summary


# Convenience function for easy usage
def create_orchestrator(
    preprocessors: Optional[List[str]] = None,
) -> PreprocessorOrchestrator:
    """
    Create a preprocessor orchestrator

    Args:
        preprocessors: Optional list of preprocessor names

    Returns:
        Configured orchestrator instance
    """
    return PreprocessorOrchestrator(preprocessors)


# Example usage function
def analyze_market_data(
    candle_data: List[Dict], orderbook_data: Optional[Dict] = None
) -> Dict:
    """
    Analyze market data using multiple preprocessors

    Args:
        candle_data: List of candle dictionaries
        orderbook_data: Optional orderbook data

    Returns:
        Comprehensive analysis results
    """
    # Create orchestrator
    orchestrator = create_orchestrator()

    # Prepare data for each processor
    data = {
        "candlestick": candle_data,
        "volume": candle_data,
        "price_action": candle_data,
        "trend": candle_data,
        "volatility": candle_data,
    }

    if orderbook_data:
        data["orderbook"] = orderbook_data

    # Process all data
    results = orchestrator.process_all(data)

    # Generate summary
    summary = orchestrator.generate_summary(results)

    return {
        "results": results,
        "summary": summary,
        "signals": orchestrator.get_combined_signals(results),
        "metrics": orchestrator.get_combined_metrics(results),
    }
