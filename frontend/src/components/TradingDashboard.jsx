import React from 'react';
import { Grid, Paper, Typography, Box, Card, CardContent } from '@mui/material';
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
  Filler
} from 'chart.js';
import SignalCard from './SignalCard';
import PositionCard from './PositionCard';
import PerformanceMetrics from './PerformanceMetrics';
import { useWebSocketContext } from '../contexts/WebSocketContext';
import '../styles/Dashboard.css';

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

const TradingDashboard = () => {
  const { 
    signals, 
    positions, 
    marketData, 
    performance, 
    priceHistory 
  } = useWebSocketContext();
  
  // Chart data preparation
  const prepareChartData = (market) => {
    const history = priceHistory[market] || [];
    
    return {
      labels: history.map(h => h.time),
      datasets: [{
        label: market,
        data: history.map(h => h.price),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1,
        fill: true
      }]
    };
  };
  
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false
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
          color: 'rgba(0, 0, 0, 0.1)'
        }
      }
    }
  };
  
  return (
    <div className="trading-dashboard">
      <Grid container spacing={3}>
        {/* Performance Overview */}
        <Grid item xs={12}>
          <PerformanceMetrics performance={performance} />
        </Grid>
        
        {/* Market Charts */}
        <Grid item xs={12} lg={8}>
          <Paper className="dashboard-paper">
            <Typography variant="h6" className="section-title">
              Market Overview
            </Typography>
            <Grid container spacing={2}>
              {Object.keys(marketData).map(market => (
                <Grid item xs={12} md={6} key={market}>
                  <Card className="market-card">
                    <CardContent>
                      <Box className="market-header">
                        <Typography variant="subtitle1">{market}</Typography>
                        <Typography variant="h6">
                          {marketData[market]?.trade_price?.toLocaleString()} KRW
                        </Typography>
                        <Typography 
                          variant="body2" 
                          className={marketData[market]?.change === 'RISE' ? 'price-up' : 'price-down'}
                        >
                          {marketData[market]?.signed_change_rate > 0 ? '+' : ''}
                          {(marketData[market]?.signed_change_rate * 100)?.toFixed(2)}%
                        </Typography>
                      </Box>
                      <Box className="chart-container" style={{ height: '150px' }}>
                        <Line data={prepareChartData(market)} options={chartOptions} />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
        
        {/* Recent Signals */}
        <Grid item xs={12} lg={4}>
          <Paper className="dashboard-paper">
            <Typography variant="h6" className="section-title">
              Recent Signals
            </Typography>
            <Box className="signals-list">
              {signals.slice(0, 5).map((signal, idx) => (
                <SignalCard key={idx} signal={signal} compact />
              ))}
              {signals.length === 0 && (
                <Typography variant="body2" color="textSecondary" align="center">
                  No signals yet
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>
        
        {/* Open Positions */}
        <Grid item xs={12}>
          <Paper className="dashboard-paper">
            <Typography variant="h6" className="section-title">
              Open Positions
            </Typography>
            <Grid container spacing={2}>
              {positions.filter(p => p.status === 'OPEN').map(position => (
                <Grid item xs={12} md={6} lg={4} key={position.position_id}>
                  <PositionCard position={position} />
                </Grid>
              ))}
              {positions.filter(p => p.status === 'OPEN').length === 0 && (
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary" align="center">
                    No open positions
                  </Typography>
                </Grid>
              )}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </div>
  );
};

export default TradingDashboard;