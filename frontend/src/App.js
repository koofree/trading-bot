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
import './styles/App.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        <Router>
          <div className="App">
            <Navigation />
            <div className="main-content">
              <Routes>
                <Route path="/" element={<TradingDashboard />} />
                <Route path="/signals" element={<SignalMonitor />} />
                <Route path="/positions" element={<PositionManager />} />
                <Route path="/analysis" element={<MarketAnalysis />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </div>
            <Toaster position="top-right" />
          </div>
        </Router>
      </WebSocketProvider>
    </QueryClientProvider>
  );
}

export default App;