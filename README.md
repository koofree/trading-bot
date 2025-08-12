# Trading Bot - AI-Powered Cryptocurrency Trading Assistant

An intelligent cryptocurrency trading bot that combines technical analysis, LLM-powered market sentiment analysis, and risk management for automated trading on Upbit exchange.

## Features

- **Real-time Trading Signals**: Generate buy/sell signals using multiple technical indicators
- **AI Market Analysis**: Leverage OpenAI GPT-4 for sentiment analysis and market insights
- **Document Processing**: Upload and analyze trading reports, PDFs, and market documents
- **Risk Management**: Built-in position sizing, stop-loss, and portfolio management
- **WebSocket Streaming**: Real-time market data and signal updates
- **Web Dashboard**: Interactive React-based UI for monitoring and control

## Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **WebSockets**: Real-time bidirectional communication
- **PostgreSQL**: Primary database for trade history and analytics
- **Redis**: Caching and real-time data management
- **OpenAI GPT-4**: LLM for market analysis
- **Pandas/NumPy**: Technical indicator calculations

### Frontend
- **React 18**: Modern UI framework
- **Material-UI**: Component library
- **Chart.js**: Data visualization
- **WebSocket Client**: Real-time updates

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Upbit API Keys
- OpenAI API Key

### Quick Start with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd trading-bot
```

2. Copy environment file and add your API keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Start with Docker Compose:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Manual Installation

#### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/trading_bot
export REDIS_URL=redis://localhost:6379
export UPBIT_ACCESS_KEY=your_key_here
export UPBIT_SECRET_KEY=your_secret_here
export OPENAI_API_KEY=your_openai_key
```

4. Initialize database:
```bash
python models/database.py
```

5. Start backend server:
```bash
uvicorn api.main:app --reload --port 8000
```

#### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Set environment variables:
```bash
export REACT_APP_API_URL=http://localhost:8000
export REACT_APP_WS_URL=ws://localhost:8000/ws
```

3. Start development server:
```bash
npm start
```

## Configuration

### Trading Parameters

Edit configuration in the Settings page or modify defaults in `backend/api/main.py`:

- `base_position_size`: Base position size (2% default)
- `risk_per_trade`: Maximum risk per trade (1% default)
- `max_positions`: Maximum concurrent positions (5 default)
- `daily_loss_limit`: Daily loss limit (5% default)
- `stop_loss_percentage`: Stop loss percentage (3% default)
- `take_profit_percentage`: Take profit percentage (6% default)

### Technical Indicators

The bot uses the following indicators:
- Moving Averages (SMA, EMA)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Volume Analysis
- Stochastic Oscillator
- ATR (Average True Range)

## API Endpoints

### WebSocket
- `/ws` - Real-time market data and trading signals

### REST API
- `GET /api/signals` - Get current trading signals
- `GET /api/positions` - Get open positions
- `GET /api/performance` - Get performance metrics
- `POST /api/execute-trade` - Execute a trade
- `POST /api/upload-report` - Upload and analyze documents
- `POST /api/config` - Update configuration

## Security

- API keys are stored encrypted
- All communications use HTTPS in production
- Rate limiting and request validation
- Secure WebSocket connections

## Risk Warning

⚠️ **IMPORTANT**: Cryptocurrency trading involves substantial risk of loss. This bot is for educational purposes. Always:
- Start with small amounts
- Test thoroughly in paper trading mode
- Never invest more than you can afford to lose
- Monitor the bot's performance regularly
- Have manual override capabilities

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm test
```

### Adding New Indicators

1. Add calculation in `backend/services/signal_generator.py`
2. Update indicator weights in configuration
3. Add visualization in frontend components

### Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check documentation in `/docs`
- Review API documentation at `/docs` endpoint

## Disclaimer

This software is provided "as is" without warranty of any kind. Use at your own risk. The authors are not responsible for any financial losses incurred through the use of this software.