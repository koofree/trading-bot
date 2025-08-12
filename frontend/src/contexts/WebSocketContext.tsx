import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import useWebSocket from 'react-use-websocket';
import toast from 'react-hot-toast';
import { 
  Signal, 
  Position, 
  MarketData, 
  Performance, 
  PriceHistory, 
  PricePoint 
} from '../types';

// WebSocket message types
interface WebSocketMessageData {
  type: 'signal' | 'market_data' | 'positions_update' | 'trade_execution' | 'performance_update' | 'subscribed';
  payload?: any;
  markets?: string[];
}

interface TradeExecutionResult {
  status: 'success' | 'failed';
  action?: string;
  reason?: string;
}

// WebSocket Context Type
interface WebSocketContextType {
  connected: boolean;
  signals: Signal[];
  positions: Position[];
  marketData: Record<string, MarketData>;
  performance: Performance;
  priceHistory: PriceHistory;
  sendMessage: (message: string) => void;
  subscribeToMarkets: (markets: string[]) => void;
  executeTrade: (signal: Signal) => void;
}

interface WebSocketProviderProps {
  children: ReactNode;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [connected, setConnected] = useState<boolean>(false);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [marketData, setMarketData] = useState<Record<string, MarketData>>({});
  const [performance, setPerformance] = useState<Performance>({
    daily_pnl: 0,
    win_rate: 0,
    total_trades: 0,
    open_positions: 0,
    max_positions: 5,
    available_balance: 0
  });
  const [priceHistory, setPriceHistory] = useState<PriceHistory>({});

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
    onError: (error: Event) => {
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

  const handleNewSignal = useCallback((signal: Signal) => {
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

  const handleMarketData = useCallback((data: { market: string; data: MarketData }) => {
    const { market, data: marketInfo } = data;
    
    setMarketData(prev => ({
      ...prev,
      [market]: marketInfo
    }));
    
    // Update price history for charts
    setPriceHistory(prev => {
      const history = prev[market] || [];
      const newPoint: PricePoint = {
        time: new Date().toLocaleTimeString(),
        price: marketInfo.trade_price
      };
      const newHistory = [...history, newPoint].slice(-50);
      
      return {
        ...prev,
        [market]: newHistory
      };
    });
  }, []);

  const handleTradeExecution = useCallback((result: TradeExecutionResult) => {
    if (result.status === 'success') {
      toast.success(`Trade executed: ${result.action}`);
    } else if (result.status === 'failed') {
      toast.error(`Trade failed: ${result.reason}`);
    }
  }, []);

  const handleWebSocketMessage = useCallback((data: WebSocketMessageData) => {
    switch(data.type) {
      case 'signal':
        handleNewSignal(data.payload as Signal);
        break;
      case 'market_data':
        handleMarketData(data.payload as { market: string; data: MarketData });
        break;
      case 'positions_update':
        setPositions(data.payload as Position[]);
        break;
      case 'trade_execution':
        handleTradeExecution(data.payload as TradeExecutionResult);
        break;
      case 'performance_update':
        setPerformance(data.payload as Performance);
        break;
      case 'subscribed':
        console.log('Subscribed to markets:', data.markets);
        break;
      default:
        console.log('Unknown message type:', (data as any).type);
    }
  }, [handleNewSignal, handleMarketData, handleTradeExecution]);

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data) as WebSocketMessageData;
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    }
  }, [lastMessage, handleWebSocketMessage]);

  const subscribeToMarkets = useCallback((markets: string[]) => {
    if (readyState === 1) { // WebSocket.OPEN
      sendMessage(JSON.stringify({
        type: 'subscribe',
        markets: markets
      }));
    }
  }, [sendMessage, readyState]);

  const executeTrade = useCallback((signal: Signal) => {
    if (readyState === 1) {
      sendMessage(JSON.stringify({
        type: 'execute_trade',
        signal: signal
      }));
    }
  }, [sendMessage, readyState]);

  const value: WebSocketContextType = {
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

export const useWebSocketContext = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within WebSocketProvider');
  }
  return context;
};