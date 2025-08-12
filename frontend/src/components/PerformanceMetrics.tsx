import React from 'react';
import { PerformanceMetricsProps } from '../types';

type ColorType = 'green' | 'red' | 'blue' | 'purple' | 'orange' | 'cyan';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactElement;
  color?: ColorType;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, subtitle, icon, color = 'blue' }) => {
  const colorClasses: Record<ColorType, string> = {
    green: 'bg-green-50 text-green-600 border-green-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    orange: 'bg-orange-50 text-orange-600 border-orange-200',
    cyan: 'bg-cyan-50 text-cyan-600 border-cyan-200'
  };
  
  const iconBgClasses: Record<ColorType, string> = {
    green: 'bg-green-100',
    red: 'bg-red-100',
    blue: 'bg-blue-100',
    purple: 'bg-purple-100',
    orange: 'bg-orange-100',
    cyan: 'bg-cyan-100'
  };
  
  return (
    <div className={`p-5 rounded-xl border ${colorClasses[color]} hover:shadow-md transition-all cursor-pointer hover:-translate-y-0.5`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-600 mb-1">{title}</p>
          <p className="text-xl font-bold">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${iconBgClasses[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ performance }) => {
  const pnlColor: ColorType = performance.daily_pnl >= 0 ? 'green' : 'red';
  
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        title="Daily P&L"
        value={`${performance.daily_pnl >= 0 ? '+' : ''}${performance.daily_pnl?.toLocaleString() || 0} KRW`}
        icon={
          performance.daily_pnl >= 0 ? (
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
            </svg>
          ) : (
            <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
            </svg>
          )
        }
        color={pnlColor}
      />
      
      <MetricCard
        title="Win Rate"
        value={`${((performance.win_rate || 0) * 100).toFixed(1)}%`}
        subtitle={`${performance.total_trades || 0} trades`}
        icon={
          <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        }
        color="orange"
      />
      
      <MetricCard
        title="Open Positions"
        value={performance.open_positions || 0}
        subtitle={`of ${performance.max_positions || 5} max`}
        icon={
          <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
        color="purple"
      />
      
      <MetricCard
        title="Available Balance"
        value={`${performance.available_balance?.toLocaleString() || 0} KRW`}
        icon={
          <svg className="w-6 h-6 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
        }
        color="cyan"
      />
    </div>
  );
};

export default PerformanceMetrics;