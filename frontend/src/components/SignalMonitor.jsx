import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useWebSocketContext } from '../contexts/WebSocketContext';
import { 
  Grid, 
  Paper, 
  Typography, 
  Box, 
  Select, 
  MenuItem, 
  FormControl, 
  InputLabel,
  Button,
  CircularProgress
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import axios from 'axios';
import SignalCard from './SignalCard';
import toast from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const SignalMonitor = () => {
  const [selectedMarket, setSelectedMarket] = useState('KRW-ETH');
  const { signals: wsSignals, executeTrade } = useWebSocketContext();
  const [displaySignals, setDisplaySignals] = useState([]);
  
  const { data: markets } = useQuery({
    queryKey: ['markets'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/markets`);
      return response.data.markets;
    }
  });
  
  // Filter WebSocket signals based on selected market
  useEffect(() => {
    if (selectedMarket === 'all') {
      setDisplaySignals(wsSignals);
    } else {
      setDisplaySignals(wsSignals.filter(s => s.market === selectedMarket));
    }
  }, [wsSignals, selectedMarket]);
  
  const { isLoading, refetch } = useQuery({
    queryKey: ['signals', selectedMarket],
    queryFn: async () => {
      const url = selectedMarket === 'all' 
        ? `${API_URL}/api/signals`
        : `${API_URL}/api/signals?market=${selectedMarket}`;
      const response = await axios.get(url);
      return response.data.signals || [];
    },
    refetchInterval: 60000, // Refetch every 60 seconds
    enabled: wsSignals.length === 0 // Only fetch if no WebSocket signals
  });
  
  const handleExecuteTrade = async (signal) => {
    try {
      // Use WebSocket for real-time execution
      executeTrade(signal);
      toast.success('Trade order sent');
    } catch (error) {
      toast.error('Failed to execute trade');
      console.error('Trade execution error:', error);
    }
  };
  
  return (
    <div className="signal-monitor">
      <Paper className="monitor-header">
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h5">Signal Monitor</Typography>
          
          <Box display="flex" gap={2} alignItems="center">
            <FormControl size="small" style={{ minWidth: 150 }}>
              <InputLabel>Market</InputLabel>
              <Select
                value={selectedMarket}
                onChange={(e) => setSelectedMarket(e.target.value)}
                label="Market"
              >
                <MenuItem value="all">All Markets</MenuItem>
                {markets?.map(market => (
                  <MenuItem key={market.market} value={market.market}>
                    {market.market}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() => refetch()}
              disabled={isLoading}
            >
              Refresh
            </Button>
          </Box>
        </Box>
      </Paper>
      
      {isLoading ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3} mt={2}>
          {displaySignals.map((signal, idx) => (
            <Grid item xs={12} md={6} lg={4} key={`${signal.market}-${idx}`}>
              <SignalCard signal={signal} />
              {signal.signal_type !== 'HOLD' && signal.strength > 0.6 && (
                <Box mt={1}>
                  <Button
                    variant="contained"
                    color={signal.signal_type === 'BUY' ? 'success' : 'error'}
                    fullWidth
                    onClick={() => handleExecuteTrade(signal)}
                  >
                    Execute {signal.signal_type}
                  </Button>
                </Box>
              )}
            </Grid>
          ))}
          
          {displaySignals.length === 0 && (
            <Grid item xs={12}>
              <Paper>
                <Box p={4} textAlign="center">
                  <Typography color="textSecondary">
                    {wsSignals.length > 0 
                      ? 'No signals available for the selected market'
                      : 'Waiting for signals...'}
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          )}
        </Grid>
      )}
    </div>
  );
};

export default SignalMonitor;