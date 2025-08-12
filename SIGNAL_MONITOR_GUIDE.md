# KRW-ETH Signal Monitor Setup Guide

## Quick Start

### 1. Prerequisites
- Python 3.8+
- Node.js 14+
- Upbit API keys (already configured in .env)

### 2. Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Frontend dependencies  
cd frontend
npm install
cd ..
```

### 3. Start the System

#### Option A: Use the provided start script
```bash
./start-local.sh
```

#### Option B: Start services individually

**Terminal 1 - Backend:**
```bash
cd backend
python api/main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### 4. Access the Application
Open browser to: http://localhost:3000

## How the Signal Monitor Works

### Signal Generation Process
1. **Market Data Collection**: Fetches 200 hourly candles from Upbit for KRW-ETH
2. **Technical Analysis**: Calculates indicators:
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - Moving Averages (SMA 20, 50, 200)
   - Bollinger Bands
   - Volume Analysis

3. **Signal Scoring**: Each indicator contributes to buy/sell scores:
   - RSI: 20% weight
   - MACD: 25% weight  
   - Moving Averages: 15% weight
   - Bollinger Bands: 15% weight
   - Volume: 10% weight
   - Sentiment (if LLM enabled): 15% weight

4. **Signal Decision**:
   - **BUY**: When buy score > 0.6 and > sell score × 1.2
   - **SELL**: When sell score > 0.6 and > buy score × 1.2
   - **HOLD**: Otherwise

### Configuration

The system is pre-configured to monitor only KRW-ETH. Key settings in `.env`:

```env
# Trading Parameters
BASE_POSITION_SIZE=0.02      # 2% of portfolio per trade
RISK_PER_TRADE=0.01          # 1% risk per trade
STOP_LOSS_PERCENTAGE=0.03    # 3% stop loss
TAKE_PROFIT_PERCENTAGE=0.06  # 6% take profit
```

### Testing the Signal Generator

Run the test script to see current KRW-ETH signals:

```bash
python test_krw_eth_signal.py
```

Example output:
```
Testing KRW-ETH Signal Monitor...
--------------------------------------------------
Fetching KRW-ETH market data...
Fetched 200 candles

Generating trading signal...

==================================================
SIGNAL ANALYSIS RESULTS
==================================================
Market: KRW-ETH
Current Price: ₩4,500,000
Signal Type: BUY
Signal Strength: 72.00%
Reasoning: RSI oversold (28.5) | MACD bullish crossover

Key Indicators:
  RSI: 28.5
  MACD: 0.0234
  SMA_20: ₩4,480,000
  SMA_50: ₩4,520,000
  Volume Ratio: 1.85x

==================================================
⚠️  STRONG BUY SIGNAL - Consider action
```

## Understanding Signals

### Signal Strength
- **> 70%**: Strong signal - High confidence
- **60-70%**: Moderate signal - Good opportunity
- **< 60%**: Weak/No signal - Wait for better setup

### Key Indicators to Watch

1. **RSI**:
   - < 30: Oversold (potential buy)
   - > 70: Overbought (potential sell)

2. **MACD**:
   - Bullish crossover: Buy signal
   - Bearish crossover: Sell signal

3. **Moving Averages**:
   - Price above MA: Bullish
   - Price below MA: Bearish
   - Golden Cross (MA50 > MA200): Strong buy
   - Death Cross (MA50 < MA200): Strong sell

4. **Volume**:
   - High volume (>1.5x average): Confirms signal
   - Low volume (<0.5x average): Weak signal

## API Endpoints

- **GET /api/signals**: Get current signals
- **GET /api/signals?market=KRW-ETH**: Get KRW-ETH signals only
- **WebSocket ws://localhost:8000/ws**: Real-time updates

## Monitoring Tips

1. **Best Times**: Signals update every 60 seconds
2. **Signal Confirmation**: Wait for strength > 60% before considering trades
3. **Risk Management**: Never risk more than configured limits
4. **Market Conditions**: Signals work best in trending markets

## Troubleshooting

### Backend won't start
- Check Python dependencies: `pip install -r backend/requirements.txt`
- Verify Upbit API keys in `.env`

### Frontend won't connect
- Ensure backend is running on port 8000
- Check REACT_APP_API_URL in `.env`

### No signals appearing
- Verify market data is being fetched (check backend logs)
- Ensure KRW-ETH market is active on Upbit

## Next Steps

1. Monitor signals in real-time via the web interface
2. Adjust confidence thresholds based on risk tolerance
3. Consider enabling LLM analysis for sentiment scoring
4. Set up alerts for strong signals (>70% strength)