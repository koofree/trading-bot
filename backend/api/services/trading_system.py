import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

# Add parent directory to path for imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from api.core.config import Settings
from api.core.websocket import ConnectionManager
from services.document_processor import DocumentProcessor
from services.llm_analyzer import LLMAnalyzer
from services.market_data_preprocessor import MarketDataPreprocessor
from services.signal_generator import SignalGenerator
from services.trading_engine import TradingEngine
from services.upbit_connector import UpbitConnector

logger = logging.getLogger(__name__)


class TradingSystem:
    """Main trading system orchestrator"""

    def __init__(self, settings: Settings, manager: ConnectionManager):
        self.settings = settings
        self.manager = manager

        # Initialize components
        self.upbit = UpbitConnector(
            settings.upbit_access_key, settings.upbit_secret_key
        )

        # Initialize market data preprocessor
        self.market_preprocessor = MarketDataPreprocessor(self.upbit)

        self.signal_generator = SignalGenerator(settings.get_config_dict())

        # Configure LLM analyzer
        llm_config = {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "api_key": settings.llm_api_key,
            "base_url": settings.llm_base_url,
        }
        self.llm_analyzer = LLMAnalyzer(llm_config)

        self.trading_engine = TradingEngine(self.upbit, settings.get_config_dict())
        self.document_processor = DocumentProcessor(self.llm_analyzer)

        # State management
        self.is_running = False
        self.monitored_markets = settings.markets
        self.signal_task: Optional[asyncio.Task] = None
        self.market_data_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the trading system"""
        if not self.is_running:
            self.is_running = True
            await self.trading_engine.initialize()

            # Start background tasks
            self.signal_task = asyncio.create_task(self._generate_signals_loop())
            self.market_data_task = asyncio.create_task(self._stream_market_data())

            logger.info("Trading system started")

    async def stop(self) -> None:
        """Stop the trading system"""
        if self.is_running:
            self.is_running = False

            if self.signal_task:
                self.signal_task.cancel()
            if self.market_data_task:
                self.market_data_task.cancel()

            await self.trading_engine.shutdown()

            logger.info("Trading system stopped")

    async def _generate_signals_loop(self) -> None:
        """Background task to generate trading signals"""
        while self.is_running:
            try:
                for market in self.monitored_markets:
                    # Get enriched market data using preprocessor
                    enriched_data = self.market_preprocessor.get_enriched_market_data(
                        market
                    )

                    # Get candles for signal generation
                    candles = self.upbit.get_candles(market, "minutes", 60, 200)

                    if candles and enriched_data:
                        # Convert to DataFrame for technical analysis
                        df = pd.DataFrame(candles)
                        df = df.rename(
                            columns={
                                "trade_price": "close",
                                "opening_price": "open",
                                "high_price": "high",
                                "low_price": "low",
                                "candle_acc_trade_volume": "volume",
                                "candle_date_time_kst": "timestamp",
                            }
                        )
                        df["market"] = market

                        # Get LLM analysis with properly preprocessed data
                        sentiment = await self.llm_analyzer.analyze_market_sentiment(
                            [], enriched_data, []
                        )

                        llm_analysis = {
                            "sentiment_score": sentiment.score,
                            "confidence": sentiment.confidence,
                            "summary": sentiment.reasoning,
                        }

                        # Generate signal
                        signal = self.signal_generator.generate_signal(df, llm_analysis)

                        # Broadcast signal
                        await self.manager.broadcast(
                            {"type": "signal", "payload": signal.to_dict()}
                        )

                        # Execute signal if confidence is high
                        if signal.strength > self.settings.min_confidence:
                            result = await self.trading_engine.execute_signal(signal)

                            await self.manager.broadcast(
                                {"type": "trade_execution", "payload": result}
                            )

                await asyncio.sleep(self.settings.signal_check_interval)

            except Exception as e:
                logger.error(f"Error in signal generation loop: {e}")
                await asyncio.sleep(30)

    async def _stream_market_data(self) -> None:
        """Stream real-time market data via WebSocket"""
        while self.is_running:
            try:
                for market in self.monitored_markets:
                    ticker = self.upbit.get_ticker([market])

                    if ticker:
                        await self.manager.broadcast(
                            {
                                "type": "market_data",
                                "payload": {
                                    "market": market,
                                    "data": ticker[0],
                                    "timestamp": datetime.now().isoformat(),
                                },
                            }
                        )

                # Also broadcast position updates
                positions = [
                    p.to_dict() for p in self.trading_engine.positions.values()
                ]
                await self.manager.broadcast(
                    {"type": "positions_update", "payload": positions}
                )

                await asyncio.sleep(5)  # Update every 5 seconds

            except Exception as e:
                logger.error(f"Error in market data stream: {e}")
                await asyncio.sleep(10)

    def get_signals(self, markets: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get current trading signals for specified markets"""
        if not markets:
            markets = self.monitored_markets

        signals = []

        for market in markets:
            try:
                # Get enriched market data
                logger.info(f"Fetching enriched data for market: {market}")
                enriched_data = self.market_preprocessor.get_enriched_market_data(
                    market
                )

                # Log enriched data for debugging
                logger.info(
                    f"Enriched data: Price={enriched_data.get('current_price', 0):,.0f}, "
                    f"24h Change={enriched_data.get('price_change_24h', 0):.2f}%, "
                    f"Volume Ratio={enriched_data.get('volume_ratio', 0):.2f}"
                )

                # Get candles for technical analysis
                candles = self.upbit.get_candles(market, "minutes", 60, 200)

                if not candles:
                    logger.warning(f"No candle data received for {market}")
                    continue

                logger.info(f"Received {len(candles)} candles for {market}")

                # Convert to DataFrame and rename columns
                df = pd.DataFrame(candles)
                df = df.rename(
                    columns={
                        "trade_price": "close",
                        "opening_price": "open",
                        "high_price": "high",
                        "low_price": "low",
                        "candle_acc_trade_volume": "volume",
                        "candle_date_time_kst": "timestamp",
                    }
                )
                df["market"] = market

                # Generate signal with enriched data context
                # Create simple LLM analysis from enriched data
                llm_analysis = {
                    "sentiment_score": 0.5
                    if enriched_data.get("momentum") == "bullish"
                    else -0.5
                    if enriched_data.get("momentum") == "bearish"
                    else 0,
                    "confidence": 0.7
                    if enriched_data.get("volume_ratio", 1) > 1.2
                    else 0.5,
                    "summary": f"{enriched_data.get('momentum', 'neutral')} momentum with {enriched_data.get('price_change_24h', 0):.1f}% change",
                }

                signal = self.signal_generator.generate_signal(df, llm_analysis)

                # Add enriched data to signal
                signal_dict = signal.to_dict()
                signal_dict["market_data"] = {
                    "current_price": enriched_data.get("current_price"),
                    "price_change_24h": enriched_data.get("price_change_24h"),
                    "volume_24h": enriched_data.get("volume_24h_quote"),
                    "momentum": enriched_data.get("momentum"),
                }

                signals.append(signal_dict)

            except Exception as e:
                logger.error(
                    f"Error processing signals for {market}: {e}", exc_info=True
                )
                continue

        return signals

    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process uploaded document"""
        analysis = await self.document_processor.process_document(file_path)

        # Broadcast update
        await self.manager.broadcast(
            {
                "type": "document_processed",
                "payload": {
                    "filename": os.path.basename(file_path),
                    "analysis": analysis,
                },
            }
        )

        return analysis
