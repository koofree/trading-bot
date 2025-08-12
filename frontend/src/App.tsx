import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { WebSocketProvider } from './contexts/WebSocketContext';
import TradingDashboard from './components/TradingDashboard';
import SignalMonitor from './components/SignalMonitor';
import PositionManager from './components/PositionManager';
import MarketAnalysis from './components/MarketAnalysis';
import Settings from './components/Settings';
import Navigation from './components/Navigation';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 30000, // 30 seconds
    },
  },
});

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        <Router>
          <div className="min-h-screen flex flex-col">
            <Navigation />
            <div className="flex-1 p-6 max-w-7xl mx-auto w-full">
              <Routes>
                <Route path="/" element={<TradingDashboard />} />
                <Route path="/signals" element={<SignalMonitor />} />
                <Route path="/positions" element={<PositionManager />} />
                <Route path="/analysis" element={<MarketAnalysis />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </div>
            <Toaster 
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
                success: {
                  style: {
                    background: '#10b981',
                  },
                },
                error: {
                  style: {
                    background: '#ef4444',
                  },
                },
              }}
            />
          </div>
        </Router>
      </WebSocketProvider>
    </QueryClientProvider>
  );
};

export default App;