import type React from 'react';
import type { SignalCardProps } from '../types';

const SignalCard: React.FC<SignalCardProps> = ({ signal, compact = false }) => {
  const getSignalIcon = (): React.ReactElement => {
    switch (signal.signal_type) {
      case 'BUY':
        return (
          <svg
            className="w-5 h-5 text-green-500"
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
        );
      case 'SELL':
        return (
          <svg
            className="w-5 h-5 text-red-500"
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
        );
      default:
        return (
          <svg
            className="w-5 h-5 text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        );
    }
  };

  const getSignalColor = (): string => {
    switch (signal.signal_type) {
      case 'BUY':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'SELL':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const formatNumber = (num: number | undefined, decimals = 2): string => {
    if (num === undefined || num === null) return 'N/A';
    return num.toFixed(decimals);
  };

  // Extract preprocessed data
  const analysis = signal.preprocessor_analysis;
  const trend = analysis?.indicators?.trend;
  const volume = analysis?.indicators?.volume;
  const volatility = analysis?.market_conditions?.volatility;
  const priceAction = analysis?.patterns?.price_action;
  const candlestick = analysis?.patterns?.candlestick;

  if (compact) {
    return (
      <div className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getSignalIcon()}
            <span className="font-medium text-gray-700">{signal.market}</span>
          </div>
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${getSignalColor()}`}>
            {(signal.strength * 100).toFixed(0)}%
          </span>
        </div>
        <p className="text-xs text-gray-500 mt-1">{formatTime(signal.timestamp)}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all p-4 border border-gray-100">
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-2">
          {getSignalIcon()}
          <h3 className="text-lg font-semibold text-gray-800">{signal.market}</h3>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getSignalColor()}`}>
          {signal.signal_type}
        </span>
      </div>

      <div className="mb-3">
        <p className="text-sm text-gray-600 mb-1">Signal Strength</p>
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                signal.signal_type === 'BUY'
                  ? 'bg-green-500'
                  : signal.signal_type === 'SELL'
                    ? 'bg-red-500'
                    : 'bg-gray-500'
              }`}
              style={{ width: `${signal.strength * 100}%` }}
            />
          </div>
          <span className="text-sm font-medium text-gray-700">
            {(signal.strength * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Market Overview */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-gray-50 p-2 rounded">
          <span className="text-xs text-gray-600">Price</span>
          <p className="text-sm font-semibold text-gray-800">
            {signal.price?.toLocaleString()} KRW
          </p>
        </div>
        <div className="bg-gray-50 p-2 rounded">
          <span className="text-xs text-gray-600">Position Size</span>
          <p className="text-sm font-semibold text-gray-800">{formatNumber(signal.volume, 4)}</p>
        </div>
      </div>

      {/* Preprocessed Analysis Data */}
      {analysis && (
        <div className="space-y-3 mb-3">
          {/* Trend Analysis */}
          {trend && (
            <div className="border-l-4 border-blue-400 pl-3">
              <p className="text-xs font-semibold text-gray-700 mb-1">Trend Analysis</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-600">Direction: </span>
                  <span className="font-medium capitalize">{trend.direction || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-600">Strength: </span>
                  <span className="font-medium">{formatNumber(trend.strength, 1)}%</span>
                </div>
              </div>
            </div>
          )}

          {/* Volume Analysis */}
          {volume && (
            <div className="border-l-4 border-purple-400 pl-3">
              <p className="text-xs font-semibold text-gray-700 mb-1">Volume Analysis</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-600">Phase: </span>
                  <span className="font-medium capitalize">{volume.volume_phase || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-600">MFI: </span>
                  <span className="font-medium">{formatNumber(volume.mfi, 1)}</span>
                </div>
                <div>
                  <span className="text-gray-600">OBV: </span>
                  <span className="font-medium capitalize">{volume.obv_trend || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-600">Trend: </span>
                  <span className="font-medium capitalize">{volume.volume_trend || 'N/A'}</span>
                </div>
              </div>
            </div>
          )}

          {/* Volatility */}
          {volatility && (
            <div className="border-l-4 border-orange-400 pl-3">
              <p className="text-xs font-semibold text-gray-700 mb-1">Volatility</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-600">Regime: </span>
                  <span className="font-medium capitalize">{volatility.regime || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-600">Current: </span>
                  <span className="font-medium">{formatNumber(volatility.current_volatility, 2)}%</span>
                </div>
              </div>
            </div>
          )}

          {/* Price Action */}
          {priceAction?.key_levels && (
            <div className="border-l-4 border-yellow-400 pl-3">
              <p className="text-xs font-semibold text-gray-700 mb-1">Key Levels</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-600">Support: </span>
                  <span className="font-medium">
                    {priceAction.key_levels.strong_support?.toLocaleString() || 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Resistance: </span>
                  <span className="font-medium">
                    {priceAction.key_levels.strong_resistance?.toLocaleString() || 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Candlestick Patterns */}
          {candlestick?.patterns_found && candlestick.patterns_found.length > 0 && (
            <div className="border-l-4 border-green-400 pl-3">
              <p className="text-xs font-semibold text-gray-700 mb-1">Candlestick Patterns</p>
              <div className="flex flex-wrap gap-1">
                {candlestick.patterns_found.slice(0, 3).map((pattern, index) => (
                  <span
                    key={index}
                    className="text-xs bg-gray-100 px-2 py-1 rounded capitalize"
                  >
                    {typeof pattern === 'string' ? pattern : pattern.name || 'Unknown'}
                  </span>
                ))}
              </div>
              {candlestick.candle_strength && (
                <div className="mt-1 text-xs">
                  <span className="text-gray-600">Bullish: </span>
                  <span className="text-green-600 font-medium">
                    {((candlestick.candle_strength.bullish_ratio ?? 0) * 100).toFixed(0)}%
                  </span>
                  <span className="text-gray-600 ml-2">Bearish: </span>
                  <span className="text-red-600 font-medium">
                    {((candlestick.candle_strength.bearish_ratio ?? 0) * 100).toFixed(0)}%
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Preprocessor Signals */}
          {analysis.signals && analysis.signals.length > 0 && (
            <div className="border-l-4 border-indigo-400 pl-3">
              <p className="text-xs font-semibold text-gray-700 mb-1">Analysis Signals</p>
              <div className="space-y-1">
                {analysis.signals.slice(0, 5).map((sig, index) => (
                  <div key={index} className="text-xs">
                    <span className="text-gray-600">[{sig.processor}]</span>{' '}
                    <span className="text-gray-800">{sig.signal}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {signal.reasoning && (
        <div className="mb-3">
          <p className="text-sm text-gray-600 mb-1">Reasoning:</p>
          <p className="text-xs text-gray-700 bg-gray-50 p-2 rounded whitespace-pre-line">
            {signal.reasoning}
          </p>
        </div>
      )}

      <p className="text-xs text-gray-500">{formatTime(signal.timestamp)}</p>
    </div>
  );
};

export default SignalCard;