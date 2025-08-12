// Market Data Types
export interface MarketData {
  market: string;
  trade_price: number;
  change: 'RISE' | 'FALL' | 'EVEN';
  signed_change_rate: number;
  acc_trade_volume_24h: number;
  high_price: number;
  low_price: number;
  opening_price: number;
  prev_closing_price: number;
  timestamp: string;
}

// Signal Types
export interface Signal {
  signal_id: string;
  market: string;
  signal_type: 'BUY' | 'SELL' | 'HOLD';
  strength: number;
  price: number;
  volume: number;
  reasoning?: string;
  timestamp: string;
  confidence?: number;
  indicators?: {
    rsi?: number;
    macd?: number;
    bollinger?: string;
    volume_ratio?: number;
  };
}

// Position Types
export interface Position {
  position_id: string;
  market: string;
  side: 'BUY' | 'SELL';
  status: 'OPEN' | 'CLOSED' | 'PENDING';
  entry_price: number;
  current_price: number;
  volume: number;
  filled_volume: number;
  pnl: number;
  pnl_percentage: number;
  stop_loss?: number;
  take_profit?: number;
  opened_at: string;
  closed_at?: string;
  order_id?: string;
}

// Performance Types
export interface Performance {
  daily_pnl: number;
  weekly_pnl?: number;
  monthly_pnl?: number;
  total_pnl?: number;
  win_rate: number;
  total_trades: number;
  winning_trades?: number;
  losing_trades?: number;
  open_positions: number;
  max_positions: number;
  available_balance: number;
  total_balance?: number;
  roi?: number;
}

// Price History Types
export interface PricePoint {
  time: string;
  price: number;
  volume?: number;
}

export type PriceHistory = Record<string, PricePoint[]>;

// Configuration Types
export interface TradingConfig {
  base_position_size: number;
  risk_per_trade: number;
  max_positions: number;
  daily_loss_limit: number;
  stop_loss_percentage: number;
  take_profit_percentage: number;
  trailing_stop?: boolean;
  trailing_stop_percentage?: number;
}

export interface ApiConfig {
  exchange_api_key: string;
  exchange_secret_key: string;
  llm_api_key: string;
  llm_provider: 'openai' | 'anthropic' | 'ollama' | 'lmstudio' | 'vllm';
  llm_model?: string;
}

// Analysis Types
export interface MarketAnalysis {
  analysis_id: string;
  filename: string;
  extracted_data?: {
    title?: string;
    date?: string;
    market?: string;
    key_points?: string[];
    metrics?: Record<string, any>;
  };
  llm_analysis?: {
    market_sentiment: 'bullish' | 'bearish' | 'neutral';
    key_insights: string[];
    recommended_actions: string[];
    risk_factors: string[];
    confidence_score: number;
    summary: string;
  };
  created_at: string;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: 'market_update' | 'signal' | 'position_update' | 'performance_update' | 'error';
  data: any;
  timestamp: string;
}

// Component Props Types
export interface SignalCardProps {
  signal: Signal;
  compact?: boolean;
}

export interface PositionCardProps {
  position: Position;
  onClose?: (position: Position) => void;
}

export interface PerformanceMetricsProps {
  performance: Performance;
}

// Context Types
export interface WebSocketContextType {
  connected: boolean;
  signals: Signal[];
  positions: Position[];
  marketData: Record<string, MarketData>;
  performance: Performance;
  priceHistory: PriceHistory;
  executeTrade: (signal: Signal) => Promise<void>;
  closePosition: (positionId: string) => Promise<void>;
  sendMessage: (message: any) => void;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface UploadedFile {
  file_id: string;
  filename: string;
  size: number;
  uploaded_at: string;
}