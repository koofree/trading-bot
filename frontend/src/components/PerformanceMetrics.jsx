import React from 'react';
import { Paper, Grid, Typography, Box } from '@mui/material';
import { TrendingUp, TrendingDown, ShowChart, AccountBalance } from '@mui/icons-material';

const MetricCard = ({ title, value, subtitle, icon, color = '#1976d2' }) => {
  return (
    <Paper className="metric-card" elevation={1}>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography variant="caption" color="textSecondary">
            {title}
          </Typography>
          <Typography variant="h5" style={{ color }}>
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="textSecondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box className="metric-icon" style={{ backgroundColor: color + '20', color }}>
          {icon}
        </Box>
      </Box>
    </Paper>
  );
};

const PerformanceMetrics = ({ performance }) => {
  const pnlColor = performance.daily_pnl >= 0 ? '#4caf50' : '#f44336';
  
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Daily P&L"
          value={`${performance.daily_pnl >= 0 ? '+' : ''}${performance.daily_pnl?.toLocaleString()} KRW`}
          icon={performance.daily_pnl >= 0 ? <TrendingUp /> : <TrendingDown />}
          color={pnlColor}
        />
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Win Rate"
          value={`${(performance.win_rate * 100).toFixed(1)}%`}
          subtitle={`${performance.total_trades} trades`}
          icon={<ShowChart />}
          color="#ff9800"
        />
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Open Positions"
          value={performance.open_positions || 0}
          subtitle={`of ${performance.max_positions || 5} max`}
          icon={<AccountBalance />}
          color="#9c27b0"
        />
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Available Balance"
          value={`${performance.available_balance?.toLocaleString() || 0} KRW`}
          icon={<AccountBalance />}
          color="#00bcd4"
        />
      </Grid>
    </Grid>
  );
};

export default PerformanceMetrics;