from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class TradingSignal:
    """Trading signal model"""

    market: str
    action: str  # 'buy', 'sell', 'hold'
    strength: float  # Signal strength (0-1)
    price: float
    timestamp: datetime
    indicators: Dict[str, Any]
    reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "market": self.market,
            "action": self.action,
            "strength": self.strength,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "indicators": self.indicators,
            "reasoning": self.reasoning,
        }


@dataclass
class Position:
    """Trading position model"""

    market: str
    entry_price: float
    current_price: float
    quantity: float
    side: str  # 'long' or 'short'
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    opened_at: Optional[datetime] = None
    pnl: float = 0.0
    pnl_percentage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "market": self.market,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "quantity": self.quantity,
            "side": self.side,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "pnl": self.pnl,
            "pnl_percentage": self.pnl_percentage,
        }
