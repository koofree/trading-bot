import os
from functools import lru_cache
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings"""

    def __init__(self):
        # API Keys
        self.upbit_access_key: str = os.getenv("UPBIT_ACCESS_KEY", "")
        self.upbit_secret_key: str = os.getenv("UPBIT_SECRET_KEY", "")

        # LLM Configuration
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "ollama")
        self.llm_model: str = os.getenv("LLM_MODEL", "llama2")
        self.llm_api_key: str = os.getenv(
            "LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")
        )
        self.llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")

        # Trading Configuration
        self.base_position_size: float = float(os.getenv("BASE_POSITION_SIZE", "0.02"))
        self.risk_per_trade: float = float(os.getenv("RISK_PER_TRADE", "0.01"))
        self.max_positions: int = int(os.getenv("MAX_POSITIONS", "5"))
        self.daily_loss_limit: float = float(os.getenv("DAILY_LOSS_LIMIT", "0.05"))
        self.stop_loss_percentage: float = float(
            os.getenv("STOP_LOSS_PERCENTAGE", "0.03")
        )
        self.take_profit_percentage: float = float(
            os.getenv("TAKE_PROFIT_PERCENTAGE", "0.06")
        )

        # System Configuration
        self.min_confidence: float = 0.6
        self.position_check_interval: int = 10
        self.signal_check_interval: int = (
            15  # Check signals every 15 seconds for more real-time data
        )
        self.markets: list = ["KRW-ETH"]

        # Indicator weights
        self.indicator_weights: Dict[str, float] = {
            "rsi": 0.2,
            "macd": 0.25,
            "ma": 0.15,
            "bb": 0.15,
            "volume": 0.1,
            "sentiment": 0.15,
        }

    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            "base_position_size": self.base_position_size,
            "risk_per_trade": self.risk_per_trade,
            "max_positions": self.max_positions,
            "daily_loss_limit": self.daily_loss_limit,
            "stop_loss_percentage": self.stop_loss_percentage,
            "take_profit_percentage": self.take_profit_percentage,
            "min_confidence": self.min_confidence,
            "position_check_interval": self.position_check_interval,
            "signal_check_interval": self.signal_check_interval,
            "markets": self.markets,
            "indicator_weights": self.indicator_weights,
        }

    def update_config(self, config_update: Dict[str, Any]) -> None:
        """Update configuration values"""
        for key, value in config_update.items():
            if hasattr(self, key):
                setattr(self, key, value)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
