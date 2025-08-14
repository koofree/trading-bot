"""
Signal Generator
Uses market data preprocessor for analysis and exports LLM-ready format
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import pandas as pd

from services.preprocessors.factory import PreprocessorOrchestrator

logger = logging.getLogger(__name__)


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradingSignal:
    """Enhanced trading signal with preprocessor data"""

    market: str
    signal_type: SignalType
    strength: float
    price: float
    volume: float
    preprocessor_analysis: dict[str, Any]
    llm_context: str
    reasoning: str
    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            "market": self.market,
            "signal_type": self.signal_type.value,
            "strength": self.strength,
            "price": self.price,
            "volume": self.volume,
            "preprocessor_analysis": self.preprocessor_analysis,
            "llm_context": self.llm_context,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
        }


class SignalGenerator:
    """Signal generator using market data preprocessor"""

    def __init__(self, config: dict):
        self.config = config

        # Configure which preprocessors to use
        self.enabled_processors = config.get(
            "enabled_processors",
            ["candlestick", "volume", "price_action", "trend", "volatility"],
        )

        # Create orchestrator with specified processors
        self.orchestrator = PreprocessorOrchestrator(self.enabled_processors)

        # Signal generation weights
        self.signal_weights = config.get(
            "signal_weights",
            {
                "candlestick": 0.15,
                "volume": 0.15,
                "price_action": 0.25,
                "trend": 0.25,
                "volatility": 0.10,
                "llm": 0.10,
            },
        )

        # Thresholds
        self.min_confidence = config.get("min_confidence", 0.6)
        self.strong_signal_threshold = config.get("strong_signal_threshold", 0.8)

    def generate_signal(
        self,
        market_data: pd.DataFrame,
        llm_analysis: Optional[dict] = None,
        orderbook_data: Optional[dict] = None,
        current_price: Optional[float] = None,
    ) -> TradingSignal:
        """
        Generate trading signal using preprocessor analysis

        Args:
            market_data: DataFrame with OHLCV data
            llm_analysis: Optional LLM analysis results
            orderbook_data: Optional orderbook data

        Returns:
            TradingSignal with complete analysis
        """

        # Prepare data for preprocessors
        market_dict = market_data.to_dict("records")

        # Prepare data for orchestrator - each processor gets the same candle data
        processor_data = {
            "candlestick": market_dict,
            "volume": market_dict,
            "price_action": market_dict,
            "trend": market_dict,
            "volatility": market_dict,
        }

        # If we only have specific processors enabled, filter the data
        if set(self.enabled_processors) != {
            "candlestick",
            "volume",
            "price_action",
            "trend",
            "volatility",
        }:
            processor_data = {k: market_dict for k in self.enabled_processors}

        # Run preprocessor analysis through orchestrator
        preprocessor_results = self.orchestrator.process_all(processor_data)

        # Extract analysis summary
        analysis_summary = self._extract_analysis_summary(preprocessor_results)

        # Generate LLM context
        llm_context = self._format_for_llm(analysis_summary, market_data)

        # Calculate signal scores
        buy_score, sell_score, signal_reasons = self._calculate_signal_scores(
            analysis_summary, llm_analysis
        )

        # Determine final signal
        signal_type, strength = self._determine_signal(buy_score, sell_score)

        # Use current ticker price if available, otherwise use last candle close
        signal_price = current_price if current_price else market_data["close"].iloc[-1]

        # Calculate position size
        volume = self._calculate_position_size(strength, signal_price)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            signal_type, signal_reasons, analysis_summary
        )

        return TradingSignal(
            market=market_data.get("market", ["UNKNOWN"])[0]
            if "market" in market_data
            else "UNKNOWN",
            signal_type=signal_type,
            strength=strength,
            price=signal_price,
            volume=volume,
            preprocessor_analysis=analysis_summary,
            llm_context=llm_context,
            reasoning=reasoning,
            timestamp=datetime.now(),
        )

    def _extract_analysis_summary(self, results: dict) -> dict[str, Any]:
        """Extract key insights from preprocessor results"""

        summary = {
            "signals": [],
            "metrics": {},
            "patterns": {},
            "indicators": {},
            "market_conditions": {},
        }

        for processor_name, result in results.items():
            if not result.is_valid():
                continue

            # Collect all signals
            summary["signals"].extend(
                [{"processor": processor_name, "signal": sig} for sig in result.signals]
            )

            # Collect metrics
            summary["metrics"][processor_name] = result.metrics

            # Extract specific insights based on processor type
            if processor_name == "candlestick":
                summary["patterns"]["candlestick"] = {
                    "current_pattern": result.data.get("current_candle", {}),
                    "patterns_found": result.data.get("patterns", []),
                    "candle_strength": result.data.get("candle_strength", {}),
                }

            elif processor_name == "volume":
                summary["indicators"]["volume"] = {
                    "obv_trend": result.data.get("indicators", {}).get("obv_trend"),
                    "volume_phase": result.data.get("patterns", {}).get("phase"),
                    "volume_trend": result.data.get("patterns", {}).get("volume_trend"),
                    "mfi": result.data.get("indicators", {}).get("mfi"),
                }

            elif processor_name == "price_action":
                summary["patterns"]["price_action"] = {
                    "breakouts": result.data.get("breakouts", {}),
                    "key_levels": result.data.get("key_levels", {}),
                    "market_structure": result.data.get("market_structure", {}),
                }

            elif processor_name == "trend":
                summary["indicators"]["trend"] = {
                    "direction": result.data.get("trend_direction"),
                    "strength": result.data.get("trend_strength"),
                    "ma_crossovers": result.data.get("ma_crossovers", {}),
                    "trend_channel": result.data.get("trend_channel", {}),
                }

            elif processor_name == "volatility":
                summary["market_conditions"]["volatility"] = {
                    "regime": result.data.get("volatility_regime"),
                    "current_volatility": result.data.get("current_volatility"),
                    "bollinger_bands": result.data.get("bollinger_bands", {}),
                    "atr": result.data.get("atr", {}),
                }

        return summary

    def _format_for_llm(self, analysis: dict, market_data: pd.DataFrame) -> str:
        """Format analysis for LLM consumption"""

        # Current market state
        current_price = market_data["close"].iloc[-1]
        price_change_24h = (
            (market_data["close"].iloc[-1] - market_data["close"].iloc[-24])
            / market_data["close"].iloc[-24]
            * 100
            if len(market_data) >= 24
            else 0
        )

        llm_prompt = f"""
## Market Analysis Summary

### Current Market State
- Current Price: {current_price:.2f}
- 24h Change: {price_change_24h:+.2f}%
- Market Phase: {analysis.get('indicators', {}).get('volume', {}).get('volume_phase', 'Unknown')}

### Technical Indicators
"""

        # Trend Analysis
        trend_info = analysis.get("indicators", {}).get("trend", {})
        if trend_info:
            strength_value = trend_info.get("strength", 0)
            if strength_value is not None:
                llm_prompt += f"""
#### Trend
- Direction: {trend_info.get('direction', 'Unknown')}
- Strength: {strength_value:.1f}
"""
            else:
                llm_prompt += f"""
#### Trend
- Direction: {trend_info.get('direction', 'Unknown')}
- Strength: Unknown
"""

        # Volume Analysis
        volume_info = analysis.get("indicators", {}).get("volume", {})
        if volume_info:
            mfi_value = volume_info.get("mfi", 0)
            if mfi_value is not None:
                llm_prompt += f"""
#### Volume
- OBV Trend: {volume_info.get('obv_trend', 'Unknown')}
- Volume Phase: {volume_info.get('volume_phase', 'Unknown')}
- MFI: {mfi_value:.1f}
"""
            else:
                llm_prompt += f"""
#### Volume
- OBV Trend: {volume_info.get('obv_trend', 'Unknown')}
- Volume Phase: {volume_info.get('volume_phase', 'Unknown')}
- MFI: Unknown
"""

        # Volatility
        volatility_info = analysis.get("market_conditions", {}).get("volatility", {})
        if volatility_info:
            current_vol = volatility_info.get("current_volatility", 0)
            if current_vol is not None:
                llm_prompt += f"""
#### Volatility
- Regime: {volatility_info.get('regime', 'Unknown')}
- Current Volatility: {current_vol:.2f}%
"""
            else:
                llm_prompt += f"""
#### Volatility
- Regime: {volatility_info.get('regime', 'Unknown')}
- Current Volatility: Unknown
"""

        # Key Patterns
        llm_prompt += "\n### Key Patterns Detected\n"

        # Candlestick patterns
        candle_patterns = (
            analysis.get("patterns", {})
            .get("candlestick", {})
            .get("patterns_found", [])
        )
        if candle_patterns:
            llm_prompt += "#### Candlestick Patterns\n"
            for pattern in candle_patterns[:3]:  # Limit to top 3
                if isinstance(pattern, dict):
                    pattern_name = pattern.get("name", "Unknown")
                    pattern_type = pattern.get("type", "")
                    llm_prompt += f"- {pattern_name} ({pattern_type})\n"
                else:
                    llm_prompt += f"- {pattern}\n"

        # Price action breakouts
        breakouts = (
            analysis.get("patterns", {}).get("price_action", {}).get("breakouts", {})
        )
        if any(breakouts.values()):
            llm_prompt += "#### Breakouts\n"
            for breakout_type, breakout_data in breakouts.items():
                if breakout_data:
                    llm_prompt += f"- {breakout_type}: {breakout_data}\n"

        # Trading Signals
        llm_prompt += "\n### Trading Signals\n"
        signals = analysis.get("signals", [])
        for signal_data in signals[:5]:  # Limit to top 5 signals
            llm_prompt += f"- [{signal_data['processor']}] {signal_data['signal']}\n"

        llm_prompt += """
### Analysis Request
Based on the above technical analysis, provide:
1. Market sentiment assessment (bullish/bearish/neutral)
2. Key support and resistance levels to watch
3. Recommended trading action with risk assessment
4. Any additional insights or warnings
"""

        return llm_prompt

    def _calculate_signal_scores(
        self, analysis: dict, llm_analysis: Optional[dict] = None
    ) -> tuple[float, float, list[str]]:
        """Calculate buy and sell scores from analysis"""

        buy_score = 0.0
        sell_score = 0.0
        reasons = []

        # Analyze signals from each processor
        for signal_data in analysis.get("signals", []):
            signal_text = signal_data["signal"].lower()
            processor = signal_data["processor"]
            weight = self.signal_weights.get(processor, 0.1)

            # Determine signal direction
            if any(
                word in signal_text
                for word in ["bullish", "buy", "uptrend", "accumulation"]
            ):
                buy_score += weight
                reasons.append(f"[{processor}] {signal_data['signal']}")
            elif any(
                word in signal_text
                for word in ["bearish", "sell", "downtrend", "distribution"]
            ):
                sell_score += weight
                reasons.append(f"[{processor}] {signal_data['signal']}")

        # Analyze trend direction
        trend_direction = (
            analysis.get("indicators", {}).get("trend", {}).get("direction")
        )
        trend_strength = (
            analysis.get("indicators", {}).get("trend", {}).get("strength", 0)
        )

        if trend_direction == "uptrend" and abs(trend_strength) > 50:
            buy_score += self.signal_weights.get("trend", 0.25) * (
                abs(trend_strength) / 100
            )
            reasons.append(f"Strong uptrend (strength: {abs(trend_strength):.1f})")
        elif trend_direction == "downtrend" and abs(trend_strength) > 50:
            sell_score += self.signal_weights.get("trend", 0.25) * (
                abs(trend_strength) / 100
            )
            reasons.append(f"Strong downtrend (strength: {abs(trend_strength):.1f})")

        # Analyze breakouts
        breakouts = (
            analysis.get("patterns", {}).get("price_action", {}).get("breakouts", {})
        )
        if breakouts.get("resistance_break"):
            buy_score += self.signal_weights.get("price_action", 0.25) * 0.5
            reasons.append("Resistance breakout detected")
        elif breakouts.get("support_break"):
            sell_score += self.signal_weights.get("price_action", 0.25) * 0.5
            reasons.append("Support breakdown detected")

        # Volume confirmation
        volume_phase = (
            analysis.get("indicators", {}).get("volume", {}).get("volume_phase")
        )
        if volume_phase == "accumulation":
            buy_score += self.signal_weights.get("volume", 0.15) * 0.5
            reasons.append("Volume accumulation phase")
        elif volume_phase == "distribution":
            sell_score += self.signal_weights.get("volume", 0.15) * 0.5
            reasons.append("Volume distribution phase")

        # Volatility adjustment
        vol_regime = (
            analysis.get("market_conditions", {}).get("volatility", {}).get("regime")
        )
        if vol_regime in ["high", "extreme"]:
            # Reduce signal strength in high volatility
            buy_score *= 0.8
            sell_score *= 0.8
            reasons.append(f"Signal adjusted for {vol_regime} volatility")

        # LLM sentiment if available
        if llm_analysis:
            sentiment_score = llm_analysis.get("sentiment_score", 0)
            llm_weight = self.signal_weights.get("llm", 0.1)

            if sentiment_score > 0.3:
                buy_score += sentiment_score * llm_weight
                reasons.append(f"Positive LLM sentiment ({sentiment_score:.2f})")
            elif sentiment_score < -0.3:
                sell_score += abs(sentiment_score) * llm_weight
                reasons.append(f"Negative LLM sentiment ({sentiment_score:.2f})")
            else:
                # Include neutral/mild sentiment in reasoning if LLM analysis was provided
                reasons.append(f"LLM sentiment analysis ({sentiment_score:.2f})")

        return buy_score, sell_score, reasons

    def _determine_signal(
        self, buy_score: float, sell_score: float
    ) -> tuple[SignalType, float]:
        """Determine final signal type and strength"""

        # Calculate net score
        buy_score - sell_score

        # Determine signal type based on scores
        if buy_score > self.min_confidence and buy_score > sell_score * 1.2:
            signal_type = SignalType.BUY
            strength = min(buy_score, 1.0)
        elif sell_score > self.min_confidence and sell_score > buy_score * 1.2:
            signal_type = SignalType.SELL
            strength = min(sell_score, 1.0)
        else:
            signal_type = SignalType.HOLD
            strength = max(buy_score, sell_score)

        logger.info(
            f"Signal determination - Buy: {buy_score:.2f}, Sell: {sell_score:.2f}, "
            f"Signal: {signal_type.value}, Strength: {strength:.2f}"
        )

        return signal_type, strength

    def _calculate_position_size(self, strength: float, price: float) -> float:
        """Calculate position size based on signal strength"""

        base_position = self.config.get("base_position_size", 0.02)
        max_position = self.config.get("max_position_size", 0.1)

        # Scale position size with signal strength
        position_size = base_position * (
            0.5 + strength * 0.5
        )  # 50% base + 50% variable

        # Apply maximum limit
        position_size = min(position_size, max_position)

        return position_size

    def _generate_reasoning(
        self, signal_type: SignalType, reasons: list[str], analysis: dict
    ) -> str:
        """Generate detailed reasoning for the signal"""

        if not reasons:
            return f"{signal_type.value} signal based on neutral market conditions"

        # Build reasoning string
        reasoning_parts = [f"{signal_type.value} signal generated based on:"]

        # Prioritize LLM sentiment if present
        llm_reasons = [r for r in reasons if "llm sentiment" in r.lower()]
        other_reasons = [r for r in reasons if "llm sentiment" not in r.lower()]

        # Add LLM reasons first if they exist, then other top reasons
        prioritized_reasons = llm_reasons + other_reasons

        # Add top reasons (limit to 5 to ensure LLM sentiment is included)
        for reason in prioritized_reasons[:5]:
            reasoning_parts.append(f"• {reason}")

        # Add market context
        vol_regime = (
            analysis.get("market_conditions", {}).get("volatility", {}).get("regime")
        )
        if vol_regime:
            reasoning_parts.append(f"• Market volatility: {vol_regime}")

        # Add risk warning if needed
        if signal_type != SignalType.HOLD:
            if vol_regime in ["high", "extreme"]:
                reasoning_parts.append(
                    "⚠️ High volatility - use strict risk management"
                )
            elif len(reasons) < 2:
                reasoning_parts.append(
                    "⚠️ Limited confirming signals - consider smaller position"
                )

        return "\n".join(reasoning_parts)

    def export_llm_training_data(
        self,
        market_data: pd.DataFrame,
        signal: TradingSignal,
        actual_outcome: Optional[dict] = None,
    ) -> dict:
        """
        Export signal data in format suitable for LLM training

        Args:
            market_data: Historical market data
            signal: Generated signal
            actual_outcome: Optional actual market outcome for training

        Returns:
            Dictionary formatted for LLM training
        """

        training_data = {
            "timestamp": signal.timestamp.isoformat(),
            "market": signal.market,
            # Input context
            "input": {
                "llm_context": signal.llm_context,
                "preprocessor_analysis": signal.preprocessor_analysis,
                "market_snapshot": {
                    "price": signal.price,
                    "volume": market_data["volume"].iloc[-1]
                    if "volume" in market_data
                    else 0,
                    "high_24h": market_data["high"].tail(24).max()
                    if len(market_data) >= 24
                    else signal.price,
                    "low_24h": market_data["low"].tail(24).min()
                    if len(market_data) >= 24
                    else signal.price,
                },
            },
            # Generated signal
            "output": {
                "signal_type": signal.signal_type.value,
                "strength": signal.strength,
                "reasoning": signal.reasoning,
                "position_size": signal.volume,
            },
            # Training labels (if outcome provided)
            "labels": actual_outcome if actual_outcome else None,
            # Metadata
            "metadata": {
                "generator_version": "v2",
                "enabled_processors": self.enabled_processors,
                "signal_weights": self.signal_weights,
            },
        }

        return training_data
