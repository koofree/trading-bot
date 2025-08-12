import React from 'react';
import { SignalCardProps } from '../types';

const SignalCard: React.FC<SignalCardProps> = ({ signal, compact = false }) => {
  const getSignalIcon = (): React.ReactElement => {
    switch(signal.signal_type) {
      case 'BUY':
        return (
          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
          </svg>
        );
      case 'SELL':
        return (
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        );
    }
  };
  
  const getSignalColor = (): string => {
    switch(signal.signal_type) {
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
        <p className="text-xs text-gray-500 mt-1">
          {formatTime(signal.timestamp)}
        </p>
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
                signal.signal_type === 'BUY' ? 'bg-green-500' : 
                signal.signal_type === 'SELL' ? 'bg-red-500' : 'bg-gray-500'
              }`}
              style={{ width: `${signal.strength * 100}%` }}
            />
          </div>
          <span className="text-sm font-medium text-gray-700">
            {(signal.strength * 100).toFixed(1)}%
          </span>
        </div>
      </div>
      
      <div className="space-y-1 mb-3">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Price:</span>
          <span className="font-medium text-gray-800">{signal.price?.toLocaleString()} KRW</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Volume:</span>
          <span className="font-medium text-gray-800">{signal.volume?.toFixed(4)}</span>
        </div>
      </div>
      
      {signal.reasoning && (
        <div className="mb-3">
          <p className="text-sm text-gray-600 mb-1">Reasoning:</p>
          <p className="text-xs text-gray-700 bg-gray-50 p-2 rounded">
            {signal.reasoning}
          </p>
        </div>
      )}
      
      <p className="text-xs text-gray-500">
        {formatTime(signal.timestamp)}
      </p>
    </div>
  );
};

export default SignalCard;