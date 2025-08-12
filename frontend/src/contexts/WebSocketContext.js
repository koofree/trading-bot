import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import useWebSocket from 'react-use-websocket';
import toast from 'react-hot-toast';

const WebSocketContext = createContext(null);

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

export const WebSocketProvider = ({ children }) => {
  const [connected, setConnected] = useState(false);
  const [signals, setSignals] = useState([]);
  const [positions, setPositions] = useState([]);
  const [marketData, setMarketData] = useState({});
  const [performance, setPerformance] = useState({
    daily_pnl: 0,
    win_rate: 0,
    total_trades: 0,
    open_positions: 0
  });
  const [priceHistory, setPriceHistory] = useState({});

  const { sendMessage, lastMessage, readyState } = useWebSocket(WS_URL, {
    onOpen: () => {
      console.log('WebSocket connected');
      setConnected(true);
      toast.success('Connected to trading system');
      
      // Subscribe to KRW-ETH by default
      setTimeout(() => {
        sendMessage(JSON.stringify({
          type: 'subscribe',
          markets: ['KRW-ETH']
        }));
      }, 100);
    },
    onClose: () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      toast.error('Disconnected from trading system');
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      // Only show error toast if not already disconnected
      if (connected) {
        toast.error('Connection error');
      }
    },
    shouldReconnect: () => true,
    reconnectInterval: 3000,
    reconnectAttempts: 100,
    share: true  // Share the same WebSocket connection across components
  });

  const handleNewSignal = useCallback((signal) => {
    setSignals(prev => [signal, ...prev].slice(0, 50));
    
    if (signal.signal_type !== 'HOLD' && signal.strength > 0.6) {
      toast(
        <div>
          <strong>{signal.signal_type} Signal</strong>
          <p>{signal.market} - Strength: {(signal.strength * 100).toFixed(1)}%</p>
        </div>,
        {
          icon: signal.signal_type === 'BUY' ? '📈' : '📉',
          duration: 5000
        }
      );
    }
  }, []);

  const handleMarketData = useCallback((data) => {
    const { market, data: marketInfo } = data;
    
    setMarketData(prev => ({
      ...prev,
      [market]: marketInfo
    }));
    
    // Update price history for charts
    setPriceHistory(prev => {
      const history = prev[market] || [];
      const newHistory = [...history, {
        time: new Date().toLocaleTimeString(),
        price: marketInfo.trade_price
      }].slice(-50);
      
      return {
        ...prev,
        [market]: newHistory
      };
    });
  }, []);

  const handleTradeExecution = useCallback((result) => {
    if (result.status === 'success') {
      toast.success(`Trade executed: ${result.action}`);
    } else if (result.status === 'failed') {
      toast.error(`Trade failed: ${result.reason}`);
    }
  }, []);

  const handleWebSocketMessage = useCallback((data) => {
    switch(data.type) {
      case 'signal':
        handleNewSignal(data.payload);
        break;
      case 'market_data':
        handleMarketData(data.payload);
        break;
      case 'positions_update':
        setPositions(data.payload);
        break;
      case 'trade_execution':
        handleTradeExecution(data.payload);
        break;
      case 'performance_update':
        setPerformance(data.payload);
        break;
      case 'subscribed':
        console.log('Subscribed to markets:', data.markets);
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  }, [handleNewSignal, handleMarketData, handleTradeExecution]);

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    }
  }, [lastMessage, handleWebSocketMessage]);

  const subscribeToMarkets = useCallback((markets) => {
    if (readyState === 1) { // WebSocket.OPEN
      sendMessage(JSON.stringify({
        type: 'subscribe',
        markets: markets
      }));
    }
  }, [sendMessage, readyState]);

  const executeTrade = useCallback((signal) => {
    if (readyState === 1) {
      sendMessage(JSON.stringify({
        type: 'execute_trade',
        signal: signal
      }));
    }
  }, [sendMessage, readyState]);

  const value = {
    connected,
    signals,
    positions,
    marketData,
    performance,
    priceHistory,
    sendMessage,
    subscribeToMarkets,
    executeTrade
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within WebSocketProvider');
  }
  return context;
};