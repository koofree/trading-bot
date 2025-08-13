import enum
import json
import logging
import os
from datetime import datetime
from typing import Optional

import redis
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/trading_bot"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Create database engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis client
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


# Enums
class SignalTypeEnum(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class OrderStatusEnum(enum.Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class PositionStatusEnum(enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIAL = "PARTIAL"


# Database Models


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    market = Column(String(20), index=True)
    signal_type = Column(SQLEnum(SignalTypeEnum))
    strength = Column(Float)
    price = Column(Float)
    volume = Column(Float)
    indicators = Column(JSON)
    reasoning = Column(String)
    created_at = Column(DateTime, default=func.now())
    executed = Column(Boolean, default=False)

    # Relationships
    trades = relationship("Trade", back_populates="signal")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(String(20), unique=True, index=True)
    market = Column(String(20), index=True)
    side = Column(String(10))
    entry_price = Column(Float)
    current_price = Column(Float)
    volume = Column(Float)
    filled_volume = Column(Float, default=0)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    pnl = Column(Float, default=0)
    pnl_percentage = Column(Float, default=0)
    status = Column(SQLEnum(PositionStatusEnum))
    opened_at = Column(DateTime, default=func.now())
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    trades = relationship("Trade", back_populates="position")
    orders = relationship("Order", back_populates="position")


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"))
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    order_id = Column(String(100), index=True)
    market = Column(String(20))
    type = Column(String(20))  # BUY, SELL
    price = Column(Float)
    volume = Column(Float)
    fee = Column(Float, default=0)
    executed_at = Column(DateTime, default=func.now())

    # Relationships
    position = relationship("Position", back_populates="trades")
    signal = relationship("Signal", back_populates="trades")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_uuid = Column(String(100), unique=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    market = Column(String(20))
    side = Column(String(10))  # bid/ask
    order_type = Column(String(20))  # limit/market
    price = Column(Float, nullable=True)
    volume = Column(Float)
    executed_volume = Column(Float, default=0)
    remaining_volume = Column(Float)
    status = Column(SQLEnum(OrderStatusEnum))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    position = relationship("Position", back_populates="orders")


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    market = Column(String(20), index=True)
    timestamp = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    # Index for efficient queries
    __table_args__ = ({"postgresql_partition_by": "RANGE (timestamp)"},)


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0)
    win_rate = Column(Float, default=0)
    avg_win = Column(Float, default=0)
    avg_loss = Column(Float, default=0)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    created_at = Column(DateTime, default=func.now())


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(50), unique=True, index=True)
    filename = Column(String(255))
    file_path = Column(String(500))
    file_type = Column(String(20))
    extracted_data = Column(JSON)
    llm_analysis = Column(JSON)
    processed_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())


# Database Helper Functions


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


def drop_db():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)
    logger.info("Database tables dropped")


# Redis Cache Helper Functions


class RedisCache:
    """Redis cache manager for fast data access"""

    @staticmethod
    def set_market_data(market: str, data: dict, expire: int = 60):
        """Cache market data"""
        key = f"market:{market}"
        redis_client.setex(key, expire, json.dumps(data))

    @staticmethod
    def get_market_data(market: str) -> Optional[dict]:
        """Get cached market data"""
        key = f"market:{market}"
        data = redis_client.get(key)
        return json.loads(data) if data else None

    @staticmethod
    def set_signal(market: str, signal: dict, expire: int = 300):
        """Cache trading signal"""
        key = f"signal:{market}"
        redis_client.setex(key, expire, json.dumps(signal))

    @staticmethod
    def get_signal(market: str) -> Optional[dict]:
        """Get cached signal"""
        key = f"signal:{market}"
        data = redis_client.get(key)
        return json.loads(data) if data else None

    @staticmethod
    def set_position(position_id: str, position: dict):
        """Cache position data"""
        key = f"position:{position_id}"
        redis_client.set(key, json.dumps(position))

    @staticmethod
    def get_position(position_id: str) -> Optional[dict]:
        """Get cached position"""
        key = f"position:{position_id}"
        data = redis_client.get(key)
        return json.loads(data) if data else None

    @staticmethod
    def delete_position(position_id: str):
        """Delete cached position"""
        key = f"position:{position_id}"
        redis_client.delete(key)

    @staticmethod
    def set_config(config: dict):
        """Cache configuration"""
        redis_client.set("config", json.dumps(config))

    @staticmethod
    def get_config() -> Optional[dict]:
        """Get cached configuration"""
        data = redis_client.get("config")
        return json.loads(data) if data else None

    @staticmethod
    def publish_event(channel: str, event: dict):
        """Publish event to Redis pub/sub"""
        redis_client.publish(channel, json.dumps(event))

    @staticmethod
    def add_to_queue(queue_name: str, item: dict):
        """Add item to Redis queue"""
        redis_client.lpush(queue_name, json.dumps(item))

    @staticmethod
    def get_from_queue(queue_name: str, timeout: int = 1) -> Optional[dict]:
        """Get item from Redis queue with blocking"""
        result = redis_client.brpop(queue_name, timeout=timeout)
        if result:
            return json.loads(result[1])
        return None

    @staticmethod
    def get_queue_length(queue_name: str) -> int:
        """Get queue length"""
        return redis_client.llen(queue_name)


# Database Repository Classes


class SignalRepository:
    """Repository for Signal operations"""

    @staticmethod
    def create(db, signal_data: dict) -> Signal:
        """Create new signal"""
        signal = Signal(**signal_data)
        db.add(signal)
        db.commit()
        db.refresh(signal)
        return signal

    @staticmethod
    def get_recent(db, market: str = None, limit: int = 50):
        """Get recent signals"""
        query = db.query(Signal)
        if market:
            query = query.filter(Signal.market == market)
        return query.order_by(Signal.created_at.desc()).limit(limit).all()

    @staticmethod
    def mark_executed(db, signal_id: int):
        """Mark signal as executed"""
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        if signal:
            signal.executed = True
            db.commit()


class PositionRepository:
    """Repository for Position operations"""

    @staticmethod
    def create(db, position_data: dict) -> Position:
        """Create new position"""
        position = Position(**position_data)
        db.add(position)
        db.commit()
        db.refresh(position)

        # Cache position
        RedisCache.set_position(
            position.position_id,
            {
                "id": position.id,
                "market": position.market,
                "status": position.status.value,
                "entry_price": position.entry_price,
                "volume": position.volume,
            },
        )

        return position

    @staticmethod
    def get_open_positions(db):
        """Get all open positions"""
        return (
            db.query(Position).filter(Position.status == PositionStatusEnum.OPEN).all()
        )

    @staticmethod
    def update_pnl(
        db, position_id: str, current_price: float, pnl: float, pnl_percentage: float
    ):
        """Update position P&L"""
        position = (
            db.query(Position).filter(Position.position_id == position_id).first()
        )
        if position:
            position.current_price = current_price
            position.pnl = pnl
            position.pnl_percentage = pnl_percentage
            db.commit()

    @staticmethod
    def close_position(db, position_id: str):
        """Close position"""
        position = (
            db.query(Position).filter(Position.position_id == position_id).first()
        )
        if position:
            position.status = PositionStatusEnum.CLOSED
            position.closed_at = datetime.now()
            db.commit()

            # Remove from cache
            RedisCache.delete_position(position_id)


class TradeRepository:
    """Repository for Trade operations"""

    @staticmethod
    def create(db, trade_data: dict) -> Trade:
        """Create new trade"""
        trade = Trade(**trade_data)
        db.add(trade)
        db.commit()
        db.refresh(trade)
        return trade

    @staticmethod
    def get_by_position(db, position_id: int):
        """Get trades for a position"""
        return db.query(Trade).filter(Trade.position_id == position_id).all()

    @staticmethod
    def get_recent(db, limit: int = 100):
        """Get recent trades"""
        return db.query(Trade).order_by(Trade.executed_at.desc()).limit(limit).all()


class PerformanceRepository:
    """Repository for Performance metrics"""

    @staticmethod
    def update_daily_metrics(db, metrics: dict):
        """Update daily performance metrics"""
        today = datetime.now().date()

        existing = (
            db.query(PerformanceMetric)
            .filter(func.date(PerformanceMetric.date) == today)
            .first()
        )

        if existing:
            for key, value in metrics.items():
                setattr(existing, key, value)
        else:
            metric = PerformanceMetric(date=datetime.now(), **metrics)
            db.add(metric)

        db.commit()

    @staticmethod
    def get_metrics(db, days: int = 30):
        """Get performance metrics for last N days"""
        return (
            db.query(PerformanceMetric)
            .order_by(PerformanceMetric.date.desc())
            .limit(days)
            .all()
        )


# Create tables on module import
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully")
