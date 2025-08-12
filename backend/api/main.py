from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging
from dotenv import load_dotenv
import pandas as pd

# Import services
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.upbit_connector import UpbitConnector
from services.signal_generator import SignalGenerator, TradingSignal
from services.llm_analyzer import LLMAnalyzer
from services.trading_engine import TradingEngine
from services.document_processor import DocumentProcessor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Trading Bot API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
        
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)

# Initialize connection manager
manager = ConnectionManager()

# Trading System Class
class TradingSystem:
    def __init__(self):
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.upbit = UpbitConnector(
            os.getenv('UPBIT_ACCESS_KEY', ''),
            os.getenv('UPBIT_SECRET_KEY', '')
        )
        
        self.signal_generator = SignalGenerator(self.config)
        
        # Configure LLM provider from environment or use defaults
        llm_config = {
            'provider': os.getenv('LLM_PROVIDER', 'ollama'),
            'model': os.getenv('LLM_MODEL', 'llama2'),
            'api_key': os.getenv('LLM_API_KEY', os.getenv('OPENAI_API_KEY', '')),
            'base_url': os.getenv('LLM_BASE_URL', 'http://localhost:11434')
        }
        self.llm_analyzer = LLMAnalyzer(llm_config)
        
        self.trading_engine = TradingEngine(self.upbit, self.config)
        self.document_processor = DocumentProcessor(self.llm_analyzer)
        
        # State management
        self.is_running = False
        self.monitored_markets = ['KRW-ETH']  # Focus only on KRW-ETH
        self.signal_task = None
        self.market_data_task = None
        
    def _load_config(self) -> Dict:
        """Load configuration from environment and defaults"""
        return {
            'base_position_size': float(os.getenv('BASE_POSITION_SIZE', 0.02)),
            'risk_per_trade': float(os.getenv('RISK_PER_TRADE', 0.01)),
            'max_positions': int(os.getenv('MAX_POSITIONS', 5)),
            'daily_loss_limit': float(os.getenv('DAILY_LOSS_LIMIT', 0.05)),
            'stop_loss_percentage': float(os.getenv('STOP_LOSS_PERCENTAGE', 0.03)),
            'take_profit_percentage': float(os.getenv('TAKE_PROFIT_PERCENTAGE', 0.06)),
            'min_confidence': 0.6,
            'position_check_interval': 10,
            'signal_check_interval': 60,
            'markets': ['KRW-ETH'],  # Focus only on KRW-ETH
            'indicator_weights': {
                'rsi': 0.2,
                'macd': 0.25,
                'ma': 0.15,
                'bb': 0.15,
                'volume': 0.1,
                'sentiment': 0.15
            }
        }
    
    async def start(self):
        """Start the trading system"""
        if not self.is_running:
            self.is_running = True
            await self.trading_engine.initialize()
            
            # Start background tasks
            self.signal_task = asyncio.create_task(self._generate_signals_loop())
            self.market_data_task = asyncio.create_task(self._stream_market_data())
            
            logger.info("Trading system started")
            
    async def stop(self):
        """Stop the trading system"""
        if self.is_running:
            self.is_running = False
            
            if self.signal_task:
                self.signal_task.cancel()
            if self.market_data_task:
                self.market_data_task.cancel()
                
            await self.trading_engine.shutdown()
            
            logger.info("Trading system stopped")
    
    async def _generate_signals_loop(self):
        """Background task to generate trading signals"""
        while self.is_running:
            try:
                for market in self.monitored_markets:
                    # Get market data
                    candles = self.upbit.get_candles(market, 'minutes', 60, 200)
                    
                    if candles:
                        # Convert to DataFrame and rename columns
                        df = pd.DataFrame(candles)
                        # Rename columns to match expected format
                        df = df.rename(columns={
                            'trade_price': 'close',
                            'opening_price': 'open',
                            'high_price': 'high',
                            'low_price': 'low',
                            'candle_acc_trade_volume': 'volume',
                            'candle_date_time_kst': 'timestamp'
                        })
                        df['market'] = market
                        
                        # Get LLM analysis
                        market_data = {
                            'current_price': candles[0]['trade_price'],
                            'volume_24h': candles[0]['candle_acc_trade_volume'],
                            'price_change_24h': candles[0]['change_rate'] if 'change_rate' in candles[0] else 0
                        }
                        
                        sentiment = await self.llm_analyzer.analyze_market_sentiment(
                            [], market_data, []
                        )
                        
                        llm_analysis = {
                            'sentiment_score': sentiment.score,
                            'confidence': sentiment.confidence,
                            'summary': sentiment.reasoning
                        }
                        
                        # Generate signal
                        signal = self.signal_generator.generate_signal(df, llm_analysis)
                        
                        # Broadcast signal
                        await manager.broadcast({
                            'type': 'signal',
                            'payload': signal.to_dict()
                        })
                        
                        # Execute signal if confidence is high
                        if signal.strength > self.config['min_confidence']:
                            result = await self.trading_engine.execute_signal(signal)
                            
                            await manager.broadcast({
                                'type': 'trade_execution',
                                'payload': result
                            })
                
                await asyncio.sleep(self.config['signal_check_interval'])
                
            except Exception as e:
                logger.error(f"Error in signal generation loop: {e}")
                await asyncio.sleep(30)
    
    async def _stream_market_data(self):
        """Stream real-time market data via WebSocket"""
        while self.is_running:
            try:
                for market in self.monitored_markets:
                    ticker = self.upbit.get_ticker([market])
                    
                    if ticker:
                        await manager.broadcast({
                            'type': 'market_data',
                            'payload': {
                                'market': market,
                                'data': ticker[0],
                                'timestamp': datetime.now().isoformat()
                            }
                        })
                
                # Also broadcast position updates
                positions = [p.to_dict() for p in self.trading_engine.positions.values()]
                await manager.broadcast({
                    'type': 'positions_update',
                    'payload': positions
                })
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in market data stream: {e}")
                await asyncio.sleep(10)

# Initialize trading system
trading_system = TradingSystem()

# API Routes

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("Starting up Trading Bot API")
    await trading_system.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Trading Bot API")
    await trading_system.stop()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Trading Bot API",
        "version": "1.0.0",
        "status": "running" if trading_system.is_running else "stopped"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse and handle WebSocket messages
            try:
                message = json.loads(data)
                await handle_websocket_message(message, websocket)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON'
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def handle_websocket_message(message: Dict, websocket: WebSocket):
    """Handle incoming WebSocket messages"""
    msg_type = message.get('type')
    
    if msg_type == 'subscribe':
        markets = message.get('markets', [])
        if markets:
            trading_system.monitored_markets = markets
            await websocket.send_text(json.dumps({
                'type': 'subscribed',
                'markets': markets
            }))
            
    elif msg_type == 'execute_trade':
        signal_data = message.get('signal')
        if signal_data:
            # Convert to TradingSignal object
            # Implementation depends on signal structure
            pass

@app.post("/api/upload-report")
async def upload_report(file: UploadFile = File(...)):
    """Handle report upload and processing"""
    try:
        # Save uploaded file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process document
        analysis = await trading_system.document_processor.process_document(file_path)
        
        # Broadcast update
        await manager.broadcast({
            'type': 'document_processed',
            'payload': {
                'filename': file.filename,
                'analysis': analysis
            }
        })
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "analysis": analysis}
        )
        
    except Exception as e:
        logger.error(f"Error uploading report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/signals")
async def get_signals(market: Optional[str] = None):
    """Get current trading signals"""
    try:
        if market:
            markets = [market]
        else:
            markets = trading_system.monitored_markets
        
        signals = []
        
        for mkt in markets:
            # Get market data
            candles = trading_system.upbit.get_candles(mkt, 'minutes', 60, 200)
            
            if candles:
                df = pd.DataFrame(candles)
                df['market'] = mkt
                
                # Generate signal without LLM for speed
                signal = trading_system.signal_generator.generate_signal(df, None)
                signals.append(signal.to_dict())
        
        return {"signals": signals}
        
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute-trade")
async def execute_trade(trade_request: Dict):
    """Execute a trading signal"""
    try:
        # Parse signal from request
        signal_data = trade_request.get('signal')
        
        if not signal_data:
            raise HTTPException(status_code=400, detail="Signal data required")
        
        # Execute trade
        # This would need proper signal parsing
        result = {"status": "not_implemented"}
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions")
async def get_positions():
    """Get current positions"""
    try:
        positions = [p.to_dict() for p in trading_system.trading_engine.positions.values()]
        return {"positions": positions}
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance")
async def get_performance():
    """Get performance metrics"""
    try:
        metrics = trading_system.trading_engine.get_performance_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
async def update_config(config_update: Dict):
    """Update trading configuration"""
    try:
        # Update configuration
        trading_system.config.update(config_update)
        trading_system.trading_engine.config.update(config_update)
        
        # Restart system with new config
        await trading_system.stop()
        await trading_system.start()
        
        return {"status": "updated", "config": trading_system.config}
        
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/markets")
async def get_markets():
    """Get available markets"""
    try:
        markets = trading_system.upbit.get_markets()
        # Filter KRW markets
        krw_markets = [m for m in markets if m['market'].startswith('KRW-')]
        return {"markets": krw_markets}
        
    except Exception as e:
        logger.error(f"Error getting markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/{market}/candles")
async def get_market_candles(market: str, interval: str = "minutes", unit: int = 60, count: int = 200):
    """Get candle data for a specific market"""
    try:
        candles = trading_system.upbit.get_candles(market, interval, unit, count)
        return {"market": market, "candles": candles}
        
    except Exception as e:
        logger.error(f"Error getting candles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backtest")
async def run_backtest(backtest_request: Dict):
    """Run backtest on historical data"""
    # This would implement backtesting logic
    return {"status": "not_implemented"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_running": trading_system.is_running
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)