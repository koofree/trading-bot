"""
Base Preprocessor Class
Abstract base class for all market data preprocessors
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PreprocessorResult:
    """Standard result format for all preprocessors"""

    processor_name: str
    timestamp: datetime
    data: Dict[str, Any]
    metrics: Dict[str, float]
    signals: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "processor": self.processor_name,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metrics": self.metrics,
            "signals": self.signals,
            "errors": self.errors,
            "metadata": self.metadata,
        }

    def is_valid(self) -> bool:
        """Check if processing was successful"""
        return len(self.errors) == 0 and len(self.data) > 0


class BasePreprocessor(ABC):
    """Abstract base class for market data preprocessors"""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize preprocessor with optional configuration

        Args:
            config: Configuration dictionary for the preprocessor
        """
        self.config = config or {}
        self.name = self.__class__.__name__

    @abstractmethod
    def process(self, data: Any) -> PreprocessorResult:
        """
        Process raw market data

        Args:
            data: Raw market data (format depends on processor)

        Returns:
            PreprocessorResult containing processed data and metrics
        """
        pass

    @abstractmethod
    def validate_input(self, data: Any) -> bool:
        """
        Validate input data format

        Args:
            data: Input data to validate

        Returns:
            True if data is valid, False otherwise
        """
        pass

    def preprocess(self, data: Any) -> PreprocessorResult:
        """
        Main entry point with validation

        Args:
            data: Raw market data

        Returns:
            PreprocessorResult with processed data or errors
        """
        # Validate input
        if not self.validate_input(data):
            return PreprocessorResult(
                processor_name=self.name,
                timestamp=datetime.now(),
                data={},
                metrics={},
                errors=[f"Invalid input data for {self.name}"],
            )

        try:
            # Process data
            result = self.process(data)
            return result
        except Exception as e:
            return PreprocessorResult(
                processor_name=self.name,
                timestamp=datetime.now(),
                data={},
                metrics={},
                errors=[f"Processing error in {self.name}: {e!s}"],
            )

    def _safe_divide(
        self, numerator: float, denominator: float, default: float = 0.0
    ) -> float:
        """Safely divide two numbers"""
        if denominator == 0:
            return default
        return numerator / denominator

    def _calculate_percentage_change(self, old_value: float, new_value: float) -> float:
        """Calculate percentage change between two values"""
        if old_value == 0:
            return 0.0
        return ((new_value - old_value) / old_value) * 100
