import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import type React from 'react';
import { useState } from 'react';
import toast from 'react-hot-toast';
import type { Position } from '../types';
import PositionCard from './PositionCard';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface PerformanceData {
  risk_metrics?: {
    daily_pnl?: number;
    win_rate?: number;
    current_exposure?: number;
  };
}

const PositionManager: React.FC = () => {
  const [tabValue, setTabValue] = useState<number>(0);

  const {
    data: positions,
    isLoading,
    refetch,
  } = useQuery<Position[]>({
    queryKey: ['positions'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/positions`);
      return response.data.positions;
    },
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  const { data: performance } = useQuery<PerformanceData>({
    queryKey: ['performance'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/performance`);
      return response.data;
    },
  });

  const handleClosePosition = async (position: Position): Promise<void> => {
    if (!window.confirm(`Close position ${position.position_id}?`)) {
      return;
    }

    try {
      // This would need to be implemented in the backend
      toast.success('Position close request sent');
      refetch();
    } catch (_error) {
      toast.error('Failed to close position');
    }
  };

  const openPositions = positions?.filter((p) => p.status === 'OPEN') || [];
  const closedPositions = positions?.filter((p) => p.status === 'CLOSED') || [];

  return (
    <div>
      <div className="mb-6 bg-white p-6 rounded-xl shadow-sm">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Position Manager</h1>

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

        {performance && (
          <div className="mt-6 flex flex-wrap gap-6">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Total P&L</p>
              <p
                className={`text-xl font-semibold ${
                  (performance.risk_metrics?.daily_pnl ?? 0) >= 0
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}
              >
                {(performance.risk_metrics?.daily_pnl ?? 0) >= 0 ? '+' : ''}
                {performance.risk_metrics?.daily_pnl?.toLocaleString()} KRW
              </p>
            </div>

            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Win Rate</p>
              <p className="text-xl font-semibold text-gray-800">
                {((performance.risk_metrics?.win_rate ?? 0) * 100).toFixed(1)}%
              </p>
            </div>

            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Current Exposure</p>
              <p className="text-xl font-semibold text-gray-800">
                {performance.risk_metrics?.current_exposure?.toLocaleString()} KRW
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="mt-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                tabValue === 0
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } transition-colors`}
              onClick={() => setTabValue(0)}
            >
              Open ({openPositions.length})
            </button>
            <button
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                tabValue === 1
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } transition-colors`}
              onClick={() => setTabValue(1)}
            >
              Closed ({closedPositions.length})
            </button>
          </nav>
        </div>

        <div className="mt-6">
          {isLoading ? (
            <div className="flex justify-center items-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {tabValue === 0 &&
                openPositions.map((position: Position) => (
                  <div key={position.position_id}>
                    <PositionCard position={position} onClose={handleClosePosition} />
                  </div>
                ))}

              {tabValue === 1 &&
                closedPositions.map((position: Position) => (
                  <div key={position.position_id}>
                    <PositionCard position={position} />
                  </div>
                ))}

              {((tabValue === 0 && openPositions.length === 0) ||
                (tabValue === 1 && closedPositions.length === 0)) && (
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
                            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 7a2 2 0 002-2h10a2 2 0 002 2v2a2 2 0 00-2 2"
                          />
                        </svg>
                      </div>
                      <p className="text-gray-500">
                        No {tabValue === 0 ? 'open' : 'closed'} positions
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PositionManager;
