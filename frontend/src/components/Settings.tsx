import React, { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import type { TradingConfig } from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface ExtendedConfig extends TradingConfig {
  min_confidence: number;
  allow_position_scaling: boolean;
  allow_short_selling: boolean;
  markets: string[];
}

interface ApiKeys {
  upbit_access_key: string;
  upbit_secret_key: string;
  openai_api_key: string;
}

interface SliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
  formatValue?: (value: number) => string;
}

const Slider: React.FC<SliderProps> = ({ label, value, onChange, min, max, step, formatValue }) => (
  <div className="mb-6">
    <div className="flex justify-between items-center mb-2">
      <label className="text-sm font-medium text-gray-700">{label}</label>
      <span className="text-sm font-semibold text-gray-800">
        {formatValue ? formatValue(value) : value}
      </span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(parseFloat(e.target.value))}
      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
    />
    <div className="flex justify-between text-xs text-gray-500 mt-1">
      <span>{formatValue ? formatValue(min) : min}</span>
      <span>{formatValue ? formatValue(max) : max}</span>
    </div>
  </div>
);

const Settings: React.FC = () => {
  const [config, setConfig] = useState<ExtendedConfig>({
    base_position_size: 0.02,
    risk_per_trade: 0.01,
    max_positions: 5,
    daily_loss_limit: 0.05,
    stop_loss_percentage: 0.03,
    take_profit_percentage: 0.06,
    min_confidence: 0.6,
    allow_position_scaling: false,
    allow_short_selling: false,
    markets: ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
  });
  
  const [apiKeys, setApiKeys] = useState<ApiKeys>({
    upbit_access_key: '',
    upbit_secret_key: '',
    openai_api_key: ''
  });
  
  const [saving, setSaving] = useState<boolean>(false);
  
  const handleConfigChange = <K extends keyof ExtendedConfig>(
    key: K, 
    value: ExtendedConfig[K]
  ): void => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };
  
  const handleApiKeyChange = <K extends keyof ApiKeys>(
    key: K, 
    value: ApiKeys[K]
  ): void => {
    setApiKeys(prev => ({
      ...prev,
      [key]: value
    }));
  };
  
  const handleSaveConfig = async (): Promise<void> => {
    setSaving(true);
    
    try {
      const response = await axios.post(`${API_URL}/api/config`, config);
      
      if (response.data.status === 'updated') {
        toast.success('Configuration saved successfully');
      }
    } catch (error) {
      toast.error('Failed to save configuration');
      console.error('Save config error:', error);
    } finally {
      setSaving(false);
    }
  };
  
  const handleResetDefaults = (): void => {
    setConfig({
      base_position_size: 0.02,
      risk_per_trade: 0.01,
      max_positions: 5,
      daily_loss_limit: 0.05,
      stop_loss_percentage: 0.03,
      take_profit_percentage: 0.06,
      min_confidence: 0.6,
      allow_position_scaling: false,
      allow_short_selling: false,
      markets: ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
    });
    
    toast.success('Configuration reset to defaults');
  };
  
  return (
    <div>
      <div className="mb-6 bg-gradient-primary text-white p-6 rounded-xl shadow-sm">
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-white/80 mt-1">Configure trading parameters and API keys</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Trading Parameters</h2>
          
          <Slider
            label="Base Position Size"
            value={config.base_position_size}
            onChange={(v) => handleConfigChange('base_position_size', v)}
            min={0.01}
            max={0.1}
            step={0.01}
            formatValue={(v) => `${(v * 100).toFixed(1)}%`}
          />
          
          <Slider
            label="Risk Per Trade"
            value={config.risk_per_trade}
            onChange={(v) => handleConfigChange('risk_per_trade', v)}
            min={0.005}
            max={0.05}
            step={0.005}
            formatValue={(v) => `${(v * 100).toFixed(1)}%`}
          />
          
          <Slider
            label="Max Positions"
            value={config.max_positions}
            onChange={(v) => handleConfigChange('max_positions', Math.round(v))}
            min={1}
            max={10}
            step={1}
          />
          
          <Slider
            label="Daily Loss Limit"
            value={config.daily_loss_limit}
            onChange={(v) => handleConfigChange('daily_loss_limit', v)}
            min={0.01}
            max={0.2}
            step={0.01}
            formatValue={(v) => `${(v * 100).toFixed(1)}%`}
          />
          
          <Slider
            label="Stop Loss"
            value={config.stop_loss_percentage}
            onChange={(v) => handleConfigChange('stop_loss_percentage', v)}
            min={0.01}
            max={0.1}
            step={0.01}
            formatValue={(v) => `${(v * 100).toFixed(1)}%`}
          />
          
          <Slider
            label="Take Profit"
            value={config.take_profit_percentage}
            onChange={(v) => handleConfigChange('take_profit_percentage', v)}
            min={0.01}
            max={0.2}
            step={0.01}
            formatValue={(v) => `${(v * 100).toFixed(1)}%`}
          />
          
          <Slider
            label="Minimum Confidence"
            value={config.min_confidence}
            onChange={(v) => handleConfigChange('min_confidence', v)}
            min={0.3}
            max={0.9}
            step={0.1}
            formatValue={(v) => `${(v * 100).toFixed(0)}%`}
          />
          
          <div className="space-y-3">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={config.allow_position_scaling}
                onChange={(e) => handleConfigChange('allow_position_scaling', e.target.checked)}
                className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
              />
              <span className="text-sm font-medium text-gray-700">
                Allow Position Scaling
              </span>
            </label>
            
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={config.allow_short_selling}
                onChange={(e) => handleConfigChange('allow_short_selling', e.target.checked)}
                className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
              />
              <span className="text-sm font-medium text-gray-700">
                Allow Short Selling
              </span>
            </label>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">API Configuration</h2>
          
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-sm text-amber-800">
                API keys are stored locally and never sent to external servers
              </p>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Upbit Access Key
              </label>
              <input
                type="password"
                value={apiKeys.upbit_access_key}
                onChange={(e) => handleApiKeyChange('upbit_access_key', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Enter Upbit access key"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Upbit Secret Key
              </label>
              <input
                type="password"
                value={apiKeys.upbit_secret_key}
                onChange={(e) => handleApiKeyChange('upbit_secret_key', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Enter Upbit secret key"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                OpenAI API Key
              </label>
              <input
                type="password"
                value={apiKeys.openai_api_key}
                onChange={(e) => handleApiKeyChange('openai_api_key', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Enter OpenAI API key"
              />
            </div>
          </div>
          
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Markets to Trade</h3>
            <div className="space-y-2">
              {['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-SOL', 'KRW-ADA'].map(market => (
                <label key={market} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.markets.includes(market)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        handleConfigChange('markets', [...config.markets, market]);
                      } else {
                        handleConfigChange('markets', config.markets.filter(m => m !== market));
                      }
                    }}
                    className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
                  />
                  <span className="text-sm text-gray-700">{market}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-6 flex justify-end gap-3">
        <button
          onClick={handleResetDefaults}
          className="px-4 py-2 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Reset to Defaults
        </button>
        
        <button
          onClick={handleSaveConfig}
          disabled={saving}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? (
            <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V2" />
            </svg>
          )}
          Save Configuration
        </button>
      </div>
      
    </div>
  );
};

export default Settings;