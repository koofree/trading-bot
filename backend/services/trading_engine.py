from dataclasses import dataclass, field
from typing import Optional, Dict, List
import asyncio
from enum import Enum
from datetime import datetime, timedelta
import logging
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

class PositionStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIAL = "PARTIAL"

@dataclass
class Position:
    position_id: str
    market: str
    side: str
    entry_price: float
    current_price: float
    volume: float
    filled_volume: float = 0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    pnl: float = 0
    pnl_percentage: float = 0
    status: PositionStatus = PositionStatus.OPEN
    opened_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
    orders: List[str] = field(default_factory=list)
    
    def update_pnl(self, current_price: float):
        """Update P&L based on current price"""
        self.current_price = current_price
        if self.side == 'buy':
            self.pnl = (current_price - self.entry_price) * self.filled_volume
            self.pnl_percentage = ((current_price / self.entry_price) - 1) * 100
        else:  # sell/short
            self.pnl = (self.entry_price - current_price) * self.filled_volume
            self.pnl_percentage = ((self.entry_price / current_price) - 1) * 100
    
    def to_dict(self):
        return {
            'position_id': self.position_id,
            'market': self.market,
            'side': self.side,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'volume': self.volume,
            'filled_volume': self.filled_volume,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'pnl': self.pnl,
            'pnl_percentage': self.pnl_percentage,
            'status': self.status.value,
            'opened_at': self.opened_at.isoformat(),
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'orders': self.orders
        }

@dataclass
class RiskMetrics:
    daily_pnl: float = 0
    daily_trades: int = 0
    win_rate: float = 0
    avg_win: float = 0
    avg_loss: float = 0
    sharpe_ratio: float = 0
    max_drawdown: float = 0
    current_exposure: float = 0
    available_balance: float = 0

class TradingEngine:
    def __init__(self, upbit_connector, config: Dict):
        self.upbit = upbit_connector
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Dict] = {}
        self.balance: Dict[str, float] = {}
        self.risk_metrics = RiskMetrics()
        self.trade_history: List[Dict] = []
        self.monitoring_task = None
        self.position_counter = 0
        
        # Risk management parameters
        self.max_positions = config.get('max_positions', 5)
        self.risk_per_trade = config.get('risk_per_trade', 0.01)
        self.daily_loss_limit = config.get('daily_loss_limit', 0.05)
        self.stop_loss_pct = config.get('stop_loss_percentage', 0.03)
        self.take_profit_pct = config.get('take_profit_percentage', 0.06)
        self.position_check_interval = config.get('position_check_interval', 10)
        
    async def initialize(self):
        """Initialize trading engine and start monitoring"""
        await self.update_balance()
        self.monitoring_task = asyncio.create_task(self.monitor_positions())
        logger.info("Trading engine initialized")
        
    async def shutdown(self):
        """Shutdown trading engine"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
        logger.info("Trading engine shutdown")
        
    async def update_balance(self):
        """Update account balance from exchange"""
        try:
            accounts = await asyncio.to_thread(self.upbit.get_accounts)
            # Check if accounts is a valid list
            if isinstance(accounts, list) and accounts:
                self.balance = {acc['currency']: float(acc['balance']) for acc in accounts}
                self.risk_metrics.available_balance = self.balance.get('KRW', 0)
                logger.info(f"Balance updated: {self.balance}")
            else:
                # Set default balance if API call failed or returned invalid data
                self.balance = {'KRW': 1000000}  # Default balance for testing
                self.risk_metrics.available_balance = 1000000
                logger.warning(f"Using default balance - API response: {accounts}")
        except Exception as e:
            logger.error(f"Error updating balance: {e}")
            # Set default balance on error
            self.balance = {'KRW': 1000000}  # Default balance for testing
            self.risk_metrics.available_balance = 1000000
            
    async def execute_signal(self, signal) -> Dict:
        """Execute trading signal with risk management"""
        
        try:
            # Pre-execution checks
            if not await self._check_risk_limits(signal):
                return {
                    "status": "rejected",
                    "reason": "Risk limit exceeded",
                    "signal": signal.to_dict() if hasattr(signal, 'to_dict') else signal
                }
            
            # Check existing position
            existing_position = self._get_open_position(signal.market)
            
            if signal.signal_type.value == "BUY":
                if existing_position:
                    if self.config.get('allow_position_scaling', False):
                        return await self._scale_position(signal, existing_position)
                    return {
                        "status": "skipped",
                        "reason": "Already in position",
                        "position": existing_position.to_dict()
                    }
                else:
                    return await self._open_position(signal)
                    
            elif signal.signal_type.value == "SELL":
                if existing_position:
                    return await self._close_position(signal, existing_position)
                else:
                    if self.config.get('allow_short_selling', False):
                        return await self._open_short_position(signal)
                    return {
                        "status": "skipped",
                        "reason": "No position to sell"
                    }
                    
            else:  # HOLD
                return {
                    "status": "hold",
                    "reason": "Hold signal - no action taken"
                }
                
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }
    
    async def _open_position(self, signal) -> Dict:
        """Open new position"""
        
        try:
            # Calculate order parameters
            order_params = self._calculate_order_params(signal)
            
            # Place order
            order_result = await asyncio.to_thread(
                self.upbit.place_order,
                market=signal.market,
                side='bid',  # buy
                volume=order_params['volume'],
                price=order_params['price'],
                ord_type=order_params['type']
            )
            
            if order_result.get('status') == 'success':
                order_data = order_result['data']
                
                # Create position record
                self.position_counter += 1
                position = Position(
                    position_id=f"POS_{self.position_counter:06d}",
                    market=signal.market,
                    side='buy',
                    entry_price=order_params['price'],
                    current_price=order_params['price'],
                    volume=order_params['volume'],
                    filled_volume=0,  # Will be updated when order fills
                    stop_loss=order_params['stop_loss'],
                    take_profit=order_params['take_profit'],
                    orders=[order_data.get('uuid', '')]
                )
                
                self.positions[position.position_id] = position
                
                # Set stop-loss and take-profit orders
                if order_params['stop_loss']:
                    asyncio.create_task(self._set_stop_loss(position))
                if order_params['take_profit']:
                    asyncio.create_task(self._set_take_profit(position))
                
                # Record trade
                self._record_trade({
                    'position_id': position.position_id,
                    'action': 'OPEN',
                    'market': signal.market,
                    'side': 'buy',
                    'price': order_params['price'],
                    'volume': order_params['volume'],
                    'signal_strength': signal.strength,
                    'reasoning': signal.reasoning,
                    'timestamp': datetime.now()
                })
                
                logger.info(f"Position opened: {position.position_id} for {signal.market}")
                
                return {
                    "status": "success",
                    "action": "position_opened",
                    "position": position.to_dict(),
                    "order_id": order_data.get('uuid', '')
                }
                
            else:
                return {
                    "status": "failed",
                    "reason": order_result.get('error', 'Order placement failed')
                }
                
        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }
    
    async def _close_position(self, signal, position: Position) -> Dict:
        """Close existing position"""
        
        try:
            # Place sell order
            order_result = await asyncio.to_thread(
                self.upbit.place_order,
                market=position.market,
                side='ask',  # sell
                volume=position.filled_volume or position.volume,
                ord_type='market'  # Market order for immediate execution
            )
            
            if order_result.get('status') == 'success':
                order_data = order_result['data']
                
                # Update position
                position.status = PositionStatus.CLOSED
                position.closed_at = datetime.now()
                position.orders.append(order_data.get('uuid', ''))
                
                # Calculate final P&L
                position.update_pnl(signal.price)
                
                # Update risk metrics
                self._update_risk_metrics(position)
                
                # Record trade
                self._record_trade({
                    'position_id': position.position_id,
                    'action': 'CLOSE',
                    'market': position.market,
                    'side': 'sell',
                    'price': signal.price,
                    'volume': position.filled_volume or position.volume,
                    'pnl': position.pnl,
                    'pnl_percentage': position.pnl_percentage,
                    'signal_strength': signal.strength,
                    'reasoning': signal.reasoning,
                    'timestamp': datetime.now()
                })
                
                logger.info(f"Position closed: {position.position_id} with P&L: {position.pnl:.2f}")
                
                return {
                    "status": "success",
                    "action": "position_closed",
                    "position": position.to_dict(),
                    "pnl": position.pnl,
                    "pnl_percentage": position.pnl_percentage
                }
                
            else:
                return {
                    "status": "failed",
                    "reason": order_result.get('error', 'Order placement failed')
                }
                
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }
    
    def _calculate_order_params(self, signal) -> Dict:
        """Calculate order parameters with risk management"""
        
        account_balance = self.balance.get('KRW', 0)
        risk_amount = account_balance * self.risk_per_trade
        
        # Position sizing based on risk
        stop_loss_distance = signal.price * self.stop_loss_pct
        position_size = risk_amount / stop_loss_distance
        
        # Apply limits
        max_position_value = account_balance * self.config.get('max_position_size', 0.1)
        position_value = min(position_size * signal.price, max_position_value)
        final_volume = position_value / signal.price
        
        # Ensure minimum order size
        min_order_size = self.config.get('min_order_size', 5000)  # 5000 KRW minimum
        if position_value < min_order_size:
            final_volume = min_order_size / signal.price
        
        # Calculate stop-loss and take-profit
        stop_loss = signal.price * (1 - self.stop_loss_pct)
        take_profit = signal.price * (1 + self.take_profit_pct)
        
        return {
            'volume': final_volume,
            'price': signal.price,
            'type': 'limit',
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
    
    async def _check_risk_limits(self, signal) -> bool:
        """Check if trade meets risk management criteria"""
        
        # Check daily loss limit
        if self.risk_metrics.daily_pnl < -(self.balance.get('KRW', 0) * self.daily_loss_limit):
            logger.warning(f"Daily loss limit reached: {self.risk_metrics.daily_pnl}")
            return False
        
        # Check maximum positions
        open_positions = [p for p in self.positions.values() if p.status == PositionStatus.OPEN]
        if len(open_positions) >= self.max_positions:
            logger.warning(f"Maximum positions reached: {len(open_positions)}")
            return False
        
        # Check correlation limit
        if self._check_correlation_limit(signal.market):
            logger.warning(f"Correlation limit exceeded for {signal.market}")
            return False
        
        # Check available balance
        required_balance = signal.price * signal.volume
        if self.balance.get('KRW', 0) < required_balance:
            logger.warning(f"Insufficient balance: {self.balance.get('KRW', 0)} < {required_balance}")
            return False
        
        return True
    
    def _check_correlation_limit(self, market: str) -> bool:
        """Check if adding this position would exceed correlation limits"""
        # Simplified correlation check - can be enhanced with actual correlation calculation
        market_base = market.split('-')[1][:3]  # Get base currency (BTC, ETH, etc.)
        
        similar_positions = 0
        for position in self.positions.values():
            if position.status == PositionStatus.OPEN:
                position_base = position.market.split('-')[1][:3]
                if position_base == market_base:
                    similar_positions += 1
        
        max_correlated = self.config.get('max_correlated_positions', 2)
        return similar_positions >= max_correlated
    
    def _get_open_position(self, market: str) -> Optional[Position]:
        """Get open position for a market"""
        for position in self.positions.values():
            if position.market == market and position.status == PositionStatus.OPEN:
                return position
        return None
    
    async def monitor_positions(self):
        """Monitor and update positions continuously"""
        while True:
            try:
                for position_id, position in list(self.positions.items()):
                    if position.status != PositionStatus.OPEN:
                        continue
                    
                    # Update current price
                    ticker = await self.upbit.async_get_ticker([position.market])
                    if ticker:
                        current_price = ticker[0]['trade_price']
                        position.update_pnl(current_price)
                        
                        # Check stop-loss
                        if position.stop_loss and current_price <= position.stop_loss:
                            logger.info(f"Stop-loss triggered for {position_id}")
                            await self._close_position_market(position, "Stop-loss triggered")
                            
                        # Check take-profit
                        elif position.take_profit and current_price >= position.take_profit:
                            logger.info(f"Take-profit triggered for {position_id}")
                            await self._close_position_market(position, "Take-profit triggered")
                
                # Update risk metrics
                self._calculate_current_exposure()
                
                await asyncio.sleep(self.position_check_interval)
                
            except Exception as e:
                logger.error(f"Error in position monitoring: {e}")
                await asyncio.sleep(self.position_check_interval)
    
    async def _close_position_market(self, position: Position, reason: str):
        """Close position with market order"""
        try:
            order_result = await asyncio.to_thread(
                self.upbit.place_order,
                market=position.market,
                side='ask',
                volume=position.filled_volume or position.volume,
                ord_type='market'
            )
            
            if order_result.get('status') == 'success':
                position.status = PositionStatus.CLOSED
                position.closed_at = datetime.now()
                logger.info(f"Position {position.position_id} closed: {reason}")
                
        except Exception as e:
            logger.error(f"Error closing position {position.position_id}: {e}")
    
    def _update_risk_metrics(self, position: Position):
        """Update risk metrics after position close"""
        self.risk_metrics.daily_pnl += position.pnl
        self.risk_metrics.daily_trades += 1
        
        if position.pnl > 0:
            wins = [t for t in self.trade_history if t.get('pnl', 0) > 0]
            self.risk_metrics.avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
        else:
            losses = [t for t in self.trade_history if t.get('pnl', 0) < 0]
            self.risk_metrics.avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
        
        # Calculate win rate
        total_closed = [t for t in self.trade_history if t.get('action') == 'CLOSE']
        wins = [t for t in total_closed if t.get('pnl', 0) > 0]
        self.risk_metrics.win_rate = len(wins) / len(total_closed) if total_closed else 0
    
    def _calculate_current_exposure(self):
        """Calculate current market exposure"""
        total_exposure = 0
        for position in self.positions.values():
            if position.status == PositionStatus.OPEN:
                total_exposure += position.current_price * position.filled_volume
        
        self.risk_metrics.current_exposure = total_exposure
    
    def _record_trade(self, trade_data: Dict):
        """Record trade in history"""
        self.trade_history.append(trade_data)
        
        # Keep only recent history (last 1000 trades)
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-1000:]
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        return {
            'risk_metrics': {
                'daily_pnl': self.risk_metrics.daily_pnl,
                'daily_trades': self.risk_metrics.daily_trades,
                'win_rate': self.risk_metrics.win_rate,
                'avg_win': self.risk_metrics.avg_win,
                'avg_loss': self.risk_metrics.avg_loss,
                'current_exposure': self.risk_metrics.current_exposure,
                'available_balance': self.risk_metrics.available_balance
            },
            'positions': {
                'open': len([p for p in self.positions.values() if p.status == PositionStatus.OPEN]),
                'total': len(self.positions)
            },
            'balance': self.balance
        }
    
    async def _set_stop_loss(self, position: Position):
        """Set stop-loss order for position"""
        # Note: Upbit doesn't support stop-loss orders directly
        # This would need to be implemented as a monitoring system
        logger.info(f"Stop-loss monitoring activated for {position.position_id} at {position.stop_loss}")
    
    async def _set_take_profit(self, position: Position):
        """Set take-profit order for position"""
        # Note: Upbit doesn't support take-profit orders directly
        # This would need to be implemented as a monitoring system
        logger.info(f"Take-profit monitoring activated for {position.position_id} at {position.take_profit}")