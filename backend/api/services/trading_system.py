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
                    # Get market data
                    candles = self.upbit.get_candles(market, "minutes", 60, 200)

                    if candles:
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

                        # Get LLM analysis
                        market_data = {
                            "current_price": candles[0]["trade_price"],
                            "volume_24h": candles[0]["candle_acc_trade_volume"],
                            "price_change_24h": candles[0].get("change_rate", 0),
                        }

                        sentiment = await self.llm_analyzer.analyze_market_sentiment(
                            [], market_data, []
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
            # Get market data
            candles = self.upbit.get_candles(market, "minutes", 60, 200)

            if candles:
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

                # Generate signal without LLM for speed
                signal = self.signal_generator.generate_signal(df, None)
                signals.append(signal.to_dict())

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
