import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartData,
  ChartOptions
} from 'chart.js';
import SignalCard from './SignalCard';
import PositionCard from './PositionCard';
import PerformanceMetrics from './PerformanceMetrics';
import { useWebSocketContext } from '../contexts/WebSocketContext';
import { MarketData } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const TradingDashboard: React.FC = () => {
  const { 
    signals, 
    positions, 
    marketData, 
    performance, 
    priceHistory 
  } = useWebSocketContext();
  
  // Chart data preparation
  const prepareChartData = (market: string): ChartData<'line'> => {
    const history = priceHistory[market] || [];
    
    return {
      labels: history.map(h => h.time),
      datasets: [{
        label: market,
        data: history.map(h => h.price),
        borderColor: 'rgb(99, 102, 241)',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        tension: 0.4,
        fill: true
      }]
    };
  };
  
  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(99, 102, 241, 0.5)',
        borderWidth: 1
      }
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false
        }
      },
      y: {
        display: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      }
    }
  };
  
  return (
    <div className="animate-fade-in">
      {/* Performance Metrics */}
      <div className="mb-6">
        <PerformanceMetrics performance={performance} />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Market Charts - Takes 2 columns on large screens */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Market Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.keys(marketData).map((market: string) => {
                const data: MarketData = marketData[market];
                const isUp = data?.change === 'RISE';
                
                return (
                  <div key={market} className="bg-gray-50 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="mb-3">
                      <div className="flex justify-between items-start">
                        <h3 className="font-medium text-gray-700">{market}</h3>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          isUp ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {isUp ? '↑' : '↓'} {Math.abs(data?.signed_change_rate * 100 || 0).toFixed(2)}%
                        </span>
                      </div>
                      <p className="text-lg font-semibold text-gray-900 mt-1">
                        {data?.trade_price?.toLocaleString()} KRW
                      </p>
                    </div>
                    <div className="h-32">
                      <Line data={prepareChartData(market)} options={chartOptions} />
                    </div>
                  </div>
                );
              })}
              {Object.keys(marketData).length === 0 && (
                <div className="col-span-2 text-center py-8 text-gray-500">
                  No market data available
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Recent Signals - Takes 1 column on large screens */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Recent Signals</h2>
              <span className="text-xs text-gray-500">{signals.length} total</span>
            </div>
            <div className="space-y-3 max-h-96 overflow-y-auto scrollbar-thin">
              {signals.slice(0, 5).map((signal, idx) => (
                <SignalCard key={idx} signal={signal} compact />
              ))}
              {signals.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No signals yet
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Open Positions */}
      <div className="mt-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-800">Open Positions</h2>
            <span className="text-xs text-gray-500">
              {positions.filter(p => p.status === 'OPEN').length} open
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {positions.filter(p => p.status === 'OPEN').map(position => (
              <PositionCard key={position.position_id} position={position} />
            ))}
            {positions.filter(p => p.status === 'OPEN').length === 0 && (
              <div className="col-span-full text-center py-8 text-gray-500">
                No open positions
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingDashboard;