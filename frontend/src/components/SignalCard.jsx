import React from 'react';
import { Card, CardContent, Typography, Chip, Box, LinearProgress } from '@mui/material';
import { TrendingUp, TrendingDown, TrendingFlat } from '@mui/icons-material';

const SignalCard = ({ signal, compact = false }) => {
  const getSignalIcon = () => {
    switch(signal.signal_type) {
      case 'BUY':
        return <TrendingUp style={{ color: '#4caf50' }} />;
      case 'SELL':
        return <TrendingDown style={{ color: '#f44336' }} />;
      default:
        return <TrendingFlat style={{ color: '#9e9e9e' }} />;
    }
  };
  
  const getSignalColor = () => {
    switch(signal.signal_type) {
      case 'BUY':
        return 'success';
      case 'SELL':
        return 'error';
      default:
        return 'default';
    }
  };
  
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };
  
  if (compact) {
    return (
      <Box className="signal-compact">
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            {getSignalIcon()}
            <Typography variant="body2">{signal.market}</Typography>
          </Box>
          <Chip 
            label={`${(signal.strength * 100).toFixed(0)}%`}
            size="small"
            color={getSignalColor()}
          />
        </Box>
        <Typography variant="caption" color="textSecondary">
          {formatTime(signal.timestamp)}
        </Typography>
      </Box>
    );
  }
  
  return (
    <Card className="signal-card">
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {getSignalIcon()}
            <Typography variant="h6">{signal.market}</Typography>
          </Box>
          <Chip 
            label={signal.signal_type}
            color={getSignalColor()}
          />
        </Box>
        
        <Box mb={2}>
          <Typography variant="body2" color="textSecondary">
            Signal Strength
          </Typography>
          <Box display="flex" alignItems="center" gap={1}>
            <LinearProgress 
              variant="determinate" 
              value={signal.strength * 100} 
              style={{ flex: 1, height: 8, borderRadius: 4 }}
              color={getSignalColor()}
            />
            <Typography variant="body2">
              {(signal.strength * 100).toFixed(1)}%
            </Typography>
          </Box>
        </Box>
        
        <Box mb={2}>
          <Typography variant="body2" color="textSecondary">
            Price: {signal.price?.toLocaleString()} KRW
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Volume: {signal.volume?.toFixed(4)}
          </Typography>
        </Box>
        
        {signal.reasoning && (
          <Box>
            <Typography variant="body2" color="textSecondary">
              Reasoning:
            </Typography>
            <Typography variant="caption">
              {signal.reasoning}
            </Typography>
          </Box>
        )}
        
        <Typography variant="caption" color="textSecondary">
          {formatTime(signal.timestamp)}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default SignalCard;