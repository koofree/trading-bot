import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class TradingSignal:
    market: str
    signal_type: SignalType
    strength: float
    price: float
    volume: float
    indicators: Dict
    reasoning: str
    timestamp: datetime
    
    def to_dict(self):
        return {
            'market': self.market,
            'signal_type': self.signal_type.value,
            'strength': self.strength,
            'price': self.price,
            'volume': self.volume,
            'indicators': self.indicators,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat()
        }

class SignalGenerator:
    def __init__(self, config: Dict):
        self.config = config
        self.indicator_weights = config.get('indicator_weights', {
            'rsi': 0.2,
            'macd': 0.25,
            'ma': 0.15,
            'bb': 0.15,
            'volume': 0.1,
            'sentiment': 0.15
        })
        
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate all technical indicators"""
        indicators = {}
        
        try:
            # Check if required columns exist
            required_columns = ['close', 'high', 'low', 'volume', 'open']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"Missing columns in DataFrame: {missing_columns}")
                logger.warning(f"Available columns: {df.columns.tolist()}")
                return indicators
            
            # Moving Averages
            indicators['sma_20'] = df['close'].rolling(window=20).mean()
            indicators['sma_50'] = df['close'].rolling(window=50).mean()
            indicators['sma_200'] = df['close'].rolling(window=200).mean()
            indicators['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            indicators['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            indicators['macd'] = indicators['ema_12'] - indicators['ema_26']
            indicators['macd_signal'] = indicators['macd'].ewm(span=9, adjust=False).mean()
            indicators['macd_histogram'] = indicators['macd'] - indicators['macd_signal']
            
            # Bollinger Bands
            sma_20 = indicators['sma_20']
            std_20 = df['close'].rolling(window=20).std()
            indicators['bb_upper'] = sma_20 + (std_20 * 2)
            indicators['bb_middle'] = sma_20
            indicators['bb_lower'] = sma_20 - (std_20 * 2)
            indicators['bb_width'] = indicators['bb_upper'] - indicators['bb_lower']
            indicators['bb_percent'] = (df['close'] - indicators['bb_lower']) / indicators['bb_width']
            
            # Volume indicators
            indicators['volume_sma'] = df['volume'].rolling(window=20).mean()
            indicators['volume_ratio'] = df['volume'] / indicators['volume_sma']
            indicators['obv'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()
            
            # Stochastic Oscillator
            low_14 = df['low'].rolling(window=14).min()
            high_14 = df['high'].rolling(window=14).max()
            indicators['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
            indicators['stoch_d'] = indicators['stoch_k'].rolling(window=3).mean()
            
            # ATR (Average True Range)
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            indicators['atr'] = true_range.rolling(window=14).mean()
            
            # Support and Resistance levels
            indicators['support'] = df['low'].rolling(window=20).min()
            indicators['resistance'] = df['high'].rolling(window=20).max()
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            
        return indicators
    
    def generate_signal(self, market_data: pd.DataFrame, 
                       llm_analysis: Optional[Dict] = None) -> TradingSignal:
        """Generate trading signal based on indicators and optional LLM analysis"""
        
        if len(market_data) < 200:
            logger.warning(f"Insufficient data for analysis: {len(market_data)} candles")
            return self._create_hold_signal(market_data, "Insufficient data")
        
        indicators = self.calculate_indicators(market_data)
        current = market_data.iloc[-1]
        
        # Initialize scoring
        buy_score = 0
        sell_score = 0
        reasons = []
        
        # RSI Analysis
        rsi_score, rsi_reason = self._analyze_rsi(indicators)
        if rsi_score > 0:
            buy_score += rsi_score * self.indicator_weights['rsi']
            reasons.append(rsi_reason)
        elif rsi_score < 0:
            sell_score += abs(rsi_score) * self.indicator_weights['rsi']
            reasons.append(rsi_reason)
        
        # MACD Analysis
        macd_score, macd_reason = self._analyze_macd(indicators)
        if macd_score > 0:
            buy_score += macd_score * self.indicator_weights['macd']
            reasons.append(macd_reason)
        elif macd_score < 0:
            sell_score += abs(macd_score) * self.indicator_weights['macd']
            reasons.append(macd_reason)
        
        # Moving Average Analysis
        ma_score, ma_reason = self._analyze_moving_averages(indicators, current)
        if ma_score > 0:
            buy_score += ma_score * self.indicator_weights['ma']
            reasons.append(ma_reason)
        elif ma_score < 0:
            sell_score += abs(ma_score) * self.indicator_weights['ma']
            reasons.append(ma_reason)
        
        # Bollinger Bands Analysis
        bb_score, bb_reason = self._analyze_bollinger_bands(indicators, current)
        if bb_score > 0:
            buy_score += bb_score * self.indicator_weights['bb']
            reasons.append(bb_reason)
        elif bb_score < 0:
            sell_score += abs(bb_score) * self.indicator_weights['bb']
            reasons.append(bb_reason)
        
        # Volume Analysis
        volume_score, volume_reason = self._analyze_volume(indicators)
        if volume_score != 0:
            if buy_score > sell_score:
                buy_score += abs(volume_score) * self.indicator_weights['volume']
            else:
                sell_score += abs(volume_score) * self.indicator_weights['volume']
            reasons.append(volume_reason)
        
        # LLM Sentiment Analysis
        if llm_analysis:
            sentiment_score = llm_analysis.get('sentiment_score', 0)
            if sentiment_score > 0.3:
                buy_score += sentiment_score * self.indicator_weights['sentiment']
                reasons.append(f"Positive sentiment ({sentiment_score:.2f})")
            elif sentiment_score < -0.3:
                sell_score += abs(sentiment_score) * self.indicator_weights['sentiment']
                reasons.append(f"Negative sentiment ({sentiment_score:.2f})")
        
        # Determine final signal
        min_confidence = self.config.get('min_confidence', 0.6)
        
        if buy_score > min_confidence and buy_score > sell_score * 1.2:
            signal_type = SignalType.BUY
            strength = min(buy_score, 1.0)
        elif sell_score > min_confidence and sell_score > buy_score * 1.2:
            signal_type = SignalType.SELL
            strength = min(sell_score, 1.0)
        else:
            signal_type = SignalType.HOLD
            strength = 0
            if not reasons:
                reasons.append("No clear signal")
        
        # Calculate position size
        volume = self._calculate_position_size(strength, current['close'])
        
        return TradingSignal(
            market=current.get('market', 'UNKNOWN'),
            signal_type=signal_type,
            strength=strength,
            price=current['close'],
            volume=volume,
            indicators={k: float(v.iloc[-1]) if hasattr(v, 'iloc') else v 
                       for k, v in indicators.items() if v is not None},
            reasoning=' | '.join(reasons) if reasons else 'No clear signals',
            timestamp=datetime.now()
        )
    
    def _analyze_rsi(self, indicators: Dict) -> tuple:
        """Analyze RSI indicator"""
        if 'rsi' not in indicators or indicators['rsi'] is None:
            return 0, ""
            
        rsi = indicators['rsi'].iloc[-1] if hasattr(indicators['rsi'], 'iloc') else indicators['rsi']
        
        if pd.isna(rsi):
            return 0, ""
            
        if rsi < 30:
            return 1.0, f"RSI oversold ({rsi:.1f})"
        elif rsi < 40:
            return 0.5, f"RSI approaching oversold ({rsi:.1f})"
        elif rsi > 70:
            return -1.0, f"RSI overbought ({rsi:.1f})"
        elif rsi > 60:
            return -0.5, f"RSI approaching overbought ({rsi:.1f})"
        
        return 0, ""
    
    def _analyze_macd(self, indicators: Dict) -> tuple:
        """Analyze MACD indicator"""
        if 'macd' not in indicators or indicators['macd'] is None:
            return 0, ""
        if 'macd_signal' not in indicators or indicators['macd_signal'] is None:
            return 0, ""
            
        macd = indicators['macd'].iloc[-1] if hasattr(indicators['macd'], 'iloc') else indicators['macd']
        macd_signal = indicators['macd_signal'].iloc[-1] if hasattr(indicators['macd_signal'], 'iloc') else indicators['macd_signal']
        macd_prev = indicators['macd'].iloc[-2] if hasattr(indicators['macd'], 'iloc') and len(indicators['macd']) > 1 else macd
        macd_signal_prev = indicators['macd_signal'].iloc[-2] if hasattr(indicators['macd_signal'], 'iloc') and len(indicators['macd_signal']) > 1 else macd_signal
        histogram = indicators['macd_histogram'].iloc[-1] if 'macd_histogram' in indicators and hasattr(indicators['macd_histogram'], 'iloc') else 0
        
        if pd.isna(macd) or pd.isna(macd_signal):
            return 0, ""
        
        # Check for crossovers
        if macd > macd_signal and macd_prev <= macd_signal_prev:
            return 1.0, "MACD bullish crossover"
        elif macd < macd_signal and macd_prev >= macd_signal_prev:
            return -1.0, "MACD bearish crossover"
        
        # Check histogram trend
        if histogram > 0 and abs(histogram) > abs(indicators['macd_histogram'].iloc[-2]):
            return 0.5, "MACD histogram strengthening (bullish)"
        elif histogram < 0 and abs(histogram) > abs(indicators['macd_histogram'].iloc[-2]):
            return -0.5, "MACD histogram strengthening (bearish)"
        
        return 0, ""
    
    def _analyze_moving_averages(self, indicators: Dict, current: pd.Series) -> tuple:
        """Analyze moving average indicators"""
        price = current['close']
        sma_20 = indicators['sma_20'].iloc[-1]
        sma_50 = indicators['sma_50'].iloc[-1]
        sma_200 = indicators['sma_200'].iloc[-1] if len(indicators['sma_200']) > 0 else None
        
        score = 0
        reasons = []
        
        # Golden/Death cross
        if not pd.isna(sma_50) and not pd.isna(sma_200) and sma_200 is not None:
            if sma_50 > sma_200 and indicators['sma_50'].iloc[-2] <= indicators['sma_200'].iloc[-2]:
                return 1.0, "Golden cross (SMA50 > SMA200)"
            elif sma_50 < sma_200 and indicators['sma_50'].iloc[-2] >= indicators['sma_200'].iloc[-2]:
                return -1.0, "Death cross (SMA50 < SMA200)"
        
        # Price relative to MAs
        if not pd.isna(sma_20):
            if price > sma_20 * 1.02:
                score += 0.3
                reasons.append("Price above SMA20")
            elif price < sma_20 * 0.98:
                score -= 0.3
                reasons.append("Price below SMA20")
        
        if not pd.isna(sma_50):
            if price > sma_50:
                score += 0.4
                reasons.append("Price above SMA50")
            else:
                score -= 0.4
                reasons.append("Price below SMA50")
        
        if reasons:
            return score, ' & '.join(reasons)
        return 0, ""
    
    def _analyze_bollinger_bands(self, indicators: Dict, current: pd.Series) -> tuple:
        """Analyze Bollinger Bands"""
        price = current['close']
        bb_upper = indicators['bb_upper'].iloc[-1]
        bb_lower = indicators['bb_lower'].iloc[-1]
        bb_percent = indicators['bb_percent'].iloc[-1]
        
        if pd.isna(bb_upper) or pd.isna(bb_lower):
            return 0, ""
        
        if price <= bb_lower:
            return 1.0, "Price at lower Bollinger Band (oversold)"
        elif bb_percent < 0.2:
            return 0.5, "Price near lower Bollinger Band"
        elif price >= bb_upper:
            return -1.0, "Price at upper Bollinger Band (overbought)"
        elif bb_percent > 0.8:
            return -0.5, "Price near upper Bollinger Band"
        
        return 0, ""
    
    def _analyze_volume(self, indicators: Dict) -> tuple:
        """Analyze volume indicators"""
        volume_ratio = indicators['volume_ratio'].iloc[-1]
        
        if pd.isna(volume_ratio):
            return 0, ""
        
        if volume_ratio > 2.0:
            return 1.0, f"Very high volume ({volume_ratio:.1f}x average)"
        elif volume_ratio > 1.5:
            return 0.5, f"High volume ({volume_ratio:.1f}x average)"
        elif volume_ratio < 0.5:
            return -0.3, f"Low volume ({volume_ratio:.1f}x average)"
        
        return 0, ""
    
    def _calculate_position_size(self, signal_strength: float, price: float) -> float:
        """Calculate position size based on signal strength and risk management"""
        base_position = self.config.get('base_position_size', 0.02)
        max_position = self.config.get('max_position_size', 0.1)
        
        position_size = base_position * signal_strength
        position_size = min(position_size, max_position)
        
        return position_size
    
    def _create_hold_signal(self, market_data: pd.DataFrame, reason: str) -> TradingSignal:
        """Create a HOLD signal with given reason"""
        current = market_data.iloc[-1] if len(market_data) > 0 else {'close': 0}
        
        return TradingSignal(
            market=current.get('market', 'UNKNOWN'),
            signal_type=SignalType.HOLD,
            strength=0,
            price=current.get('close', 0),
            volume=0,
            indicators={},
            reasoning=reason,
            timestamp=datetime.now()
        )