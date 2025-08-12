#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.upbit_connector import UpbitConnector
from services.signal_generator import SignalGenerator
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def test_krw_eth_signal():
    print("Testing KRW-ETH Signal Monitor...")
    print("-" * 50)
    
    # Initialize Upbit connector
    upbit = UpbitConnector(
        os.getenv('UPBIT_ACCESS_KEY'),
        os.getenv('UPBIT_SECRET_KEY')
    )
    
    # Get KRW-ETH market data
    market = 'KRW-ETH'
    print(f"Fetching {market} market data...")
    
    # Get 200 candles of 60-minute data
    candles = upbit.get_candles(market, 'minutes', 60, 200)
    
    if not candles:
        print("Failed to fetch market data!")
        return
    
    print(f"Fetched {len(candles)} candles")
    
    # Convert to DataFrame
    df = pd.DataFrame(candles)
    df = df.rename(columns={
        'trade_price': 'close',
        'opening_price': 'open',
        'high_price': 'high',
        'low_price': 'low',
        'candle_acc_trade_volume': 'volume',
        'candle_date_time_kst': 'timestamp'
    })
    df['market'] = market
    
    # Initialize signal generator
    config = {
        'min_confidence': 0.6,
        'base_position_size': 0.02,
        'max_position_size': 0.1,
        'indicator_weights': {
            'rsi': 0.2,
            'macd': 0.25,
            'ma': 0.15,
            'bb': 0.15,
            'volume': 0.1,
            'sentiment': 0.15
        }
    }
    
    signal_gen = SignalGenerator(config)
    
    # Generate signal
    print("\nGenerating trading signal...")
    signal = signal_gen.generate_signal(df, None)
    
    # Display results
    print("\n" + "=" * 50)
    print("SIGNAL ANALYSIS RESULTS")
    print("=" * 50)
    print(f"Market: {signal.market}")
    print(f"Current Price: ₩{signal.price:,.0f}")
    print(f"Signal Type: {signal.signal_type.value}")
    print(f"Signal Strength: {signal.strength:.2%}")
    print(f"Reasoning: {signal.reasoning}")
    
    # Display key indicators
    if signal.indicators:
        print("\nKey Indicators:")
        indicators_to_show = ['rsi', 'macd', 'sma_20', 'sma_50', 'volume_ratio']
        for key in indicators_to_show:
            if key in signal.indicators:
                value = signal.indicators[key]
                if key == 'rsi':
                    print(f"  RSI: {value:.1f}")
                elif key == 'macd':
                    print(f"  MACD: {value:.4f}")
                elif key in ['sma_20', 'sma_50']:
                    print(f"  {key.upper()}: ₩{value:,.0f}")
                elif key == 'volume_ratio':
                    print(f"  Volume Ratio: {value:.2f}x")
    
    print("\n" + "=" * 50)
    
    # Trading recommendation
    if signal.signal_type.value != 'HOLD':
        if signal.strength > 0.7:
            print(f"⚠️  STRONG {signal.signal_type.value} SIGNAL - Consider action")
        elif signal.strength > 0.6:
            print(f"📊 Moderate {signal.signal_type.value} signal - Monitor closely")
    else:
        print("✋ No clear trading signal - Continue monitoring")

if __name__ == "__main__":
    test_krw_eth_signal()