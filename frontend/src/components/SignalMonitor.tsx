import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import type React from 'react';
import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useWebSocketContext } from '../contexts/WebSocketContext';
import type { Signal } from '../types';
import SignalCard from './SignalCard';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface MarketData {
  market: string;
}

const SignalMonitor: React.FC = () => {
  const [selectedMarket, setSelectedMarket] = useState<string>('KRW-ETH');
  const { signals: wsSignals, executeTrade } = useWebSocketContext();
  const [displaySignals, setDisplaySignals] = useState<Signal[]>([]);

  const { data: markets } = useQuery<MarketData[]>({
    queryKey: ['markets'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/markets`);
      return response.data.markets;
    },
  });

  // Filter WebSocket signals based on selected market
  useEffect(() => {
    if (selectedMarket === 'all') {
      setDisplaySignals(wsSignals);
    } else {
      setDisplaySignals(wsSignals.filter((s) => s.market === selectedMarket));
    }
  }, [wsSignals, selectedMarket]);

  const { isLoading, refetch } = useQuery<Signal[]>({
    queryKey: ['signals', selectedMarket],
    queryFn: async () => {
      const url =
        selectedMarket === 'all'
          ? `${API_URL}/api/signals`
          : `${API_URL}/api/signals?market=${selectedMarket}`;
      const response = await axios.get(url);
      return response.data.signals || [];
    },
    refetchInterval: 60000, // Refetch every 60 seconds
    enabled: wsSignals.length === 0, // Only fetch if no WebSocket signals
  });

  const handleExecuteTrade = async (signal: Signal): Promise<void> => {
    try {
      // Use WebSocket for real-time execution
      executeTrade(signal);
      toast.success('Trade order sent');
    } catch (_error) {
      toast.error('Failed to execute trade');
    }
  };

  const handleMarketChange = (e: React.ChangeEvent<HTMLSelectElement>): void => {
    setSelectedMarket(e.target.value);
  };

  return (
    <div className="signal-monitor">
      <div className="mb-6 bg-white p-6 rounded-xl shadow-sm">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Signal Monitor</h1>

          <div className="flex gap-4 items-center">
            <div className="relative">
              <select
                className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent min-w-[150px]"
                value={selectedMarket}
                onChange={handleMarketChange}
              >
                <option value="all">All Markets</option>
                {markets?.map((market: MarketData) => (
                  <option key={market.market} value={market.market}>
                    {market.market}
                  </option>
                ))}
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                <svg
                  className="w-4 h-4 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </div>
            </div>

            <button
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              <svg
                className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
          {displaySignals.map((signal: Signal, idx: number) => (
            <div key={`${signal.market}-${idx}`} className="space-y-2">
              <SignalCard signal={signal} />
              {signal.signal_type !== 'HOLD' && signal.strength > 0.6 && (
                <button
                  className={`w-full py-2 px-4 rounded-lg font-medium text-white transition-colors ${
                    signal.signal_type === 'BUY'
                      ? 'bg-green-500 hover:bg-green-600 focus:ring-green-500'
                      : 'bg-red-500 hover:bg-red-600 focus:ring-red-500'
                  } focus:outline-none focus:ring-2 focus:ring-offset-2`}
                  onClick={() => handleExecuteTrade(signal)}
                >
                  Execute {signal.signal_type}
                </button>
              )}
            </div>
          ))}

          {displaySignals.length === 0 && (
            <div className="col-span-full">
              <div className="bg-white rounded-xl shadow-sm">
                <div className="p-8 text-center">
                  <div className="text-gray-400 mb-2">
                    <svg
                      className="w-12 h-12 mx-auto"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                  </div>
                  <p className="text-gray-500">
                    {wsSignals.length > 0
                      ? 'No signals available for the selected market'
                      : 'Waiting for signals...'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SignalMonitor;
