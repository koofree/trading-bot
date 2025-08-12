import type React from 'react';
import type { PositionCardProps } from '../types';

const PositionCard: React.FC<PositionCardProps> = ({ position, onClose }) => {
  const pnlColor = position.pnl >= 0 ? 'text-green-600' : 'text-red-600';
  const pnlBgColor = position.pnl >= 0 ? 'bg-green-50' : 'bg-red-50';
  const pnlBorderColor = position.pnl >= 0 ? 'border-green-200' : 'border-red-200';

  const formatDateTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all p-4 border border-gray-100">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-lg font-semibold text-gray-800">{position.market}</h3>
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${
            position.status === 'OPEN'
              ? 'bg-blue-100 text-blue-700 border border-blue-200'
              : 'bg-gray-100 text-gray-700 border border-gray-200'
          }`}
        >
          {position.status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <p className="text-xs text-gray-600">Entry Price</p>
          <p className="text-sm font-medium text-gray-800">
            {position.entry_price?.toLocaleString()} KRW
          </p>
        </div>

        <div>
          <p className="text-xs text-gray-600">Current Price</p>
          <p className="text-sm font-medium text-gray-800">
            {position.current_price?.toLocaleString()} KRW
          </p>
        </div>

        <div>
          <p className="text-xs text-gray-600">Volume</p>
          <p className="text-sm font-medium text-gray-800">{position.volume?.toFixed(4)}</p>
        </div>

        <div>
          <p className="text-xs text-gray-600">Filled</p>
          <p className="text-sm font-medium text-gray-800">{position.filled_volume?.toFixed(4)}</p>
        </div>
      </div>

      <div className={`p-3 rounded-lg border ${pnlBgColor} ${pnlBorderColor} mb-3`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {position.pnl >= 0 ? (
              <svg
                className="w-4 h-4 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 11l5-5m0 0l5 5m-5-5v12"
                />
              </svg>
            ) : (
              <svg
                className="w-4 h-4 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 13l-5 5m0 0l-5-5m5 5V6"
                />
              </svg>
            )}
            <span className="text-xs text-gray-600">P&L</span>
          </div>
          <div className="text-right">
            <p className={`text-sm font-semibold ${pnlColor}`}>
              {position.pnl >= 0 ? '+' : ''}
              {position.pnl?.toLocaleString()} KRW
            </p>
            <p className={`text-xs ${pnlColor}`}>
              ({position.pnl_percentage >= 0 ? '+' : ''}
              {position.pnl_percentage?.toFixed(2)}%)
            </p>
          </div>
        </div>
      </div>

      {(position.stop_loss || position.take_profit) && (
        <div className="space-y-1 mb-3">
          {position.stop_loss && (
            <div className="flex justify-between text-xs">
              <span className="text-gray-600">Stop Loss:</span>
              <span className="font-medium text-red-600">
                {position.stop_loss?.toLocaleString()} KRW
              </span>
            </div>
          )}
          {position.take_profit && (
            <div className="flex justify-between text-xs">
              <span className="text-gray-600">Take Profit:</span>
              <span className="font-medium text-green-600">
                {position.take_profit?.toLocaleString()} KRW
              </span>
            </div>
          )}
        </div>
      )}

      <p className="text-xs text-gray-500 mb-3">Opened: {formatDateTime(position.opened_at)}</p>

      {position.status === 'OPEN' && onClose && (
        <button
          onClick={() => onClose(position)}
          className="w-full py-2 px-4 bg-red-50 hover:bg-red-100 text-red-600 text-sm font-medium rounded-lg transition-colors border border-red-200"
        >
          Close Position
        </button>
      )}
    </div>
  );
};

export default PositionCard;
