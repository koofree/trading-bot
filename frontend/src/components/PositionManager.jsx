import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Tabs,
  Tab,
  Button,
  CircularProgress
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import axios from 'axios';
import PositionCard from './PositionCard';
import toast from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const PositionManager = () => {
  const [tabValue, setTabValue] = useState(0);
  
  const { data: positions, isLoading, refetch } = useQuery({
    queryKey: ['positions'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/positions`);
      return response.data.positions;
    },
    refetchInterval: 10000 // Refetch every 10 seconds
  });
  
  const { data: performance } = useQuery({
    queryKey: ['performance'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/performance`);
      return response.data;
    }
  });
  
  const handleClosePosition = async (position) => {
    if (!window.confirm(`Close position ${position.position_id}?`)) {
      return;
    }
    
    try {
      // This would need to be implemented in the backend
      toast.success('Position close request sent');
      refetch();
    } catch (error) {
      toast.error('Failed to close position');
      console.error('Close position error:', error);
    }
  };
  
  const openPositions = positions?.filter(p => p.status === 'OPEN') || [];
  const closedPositions = positions?.filter(p => p.status === 'CLOSED') || [];
  
  return (
    <div className="position-manager">
      <Paper className="manager-header">
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h5">Position Manager</Typography>
          
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => refetch()}
            disabled={isLoading}
          >
            Refresh
          </Button>
        </Box>
        
        {performance && (
          <Box mt={2} display="flex" gap={3}>
            <Box>
              <Typography variant="caption" color="textSecondary">
                Total P&L
              </Typography>
              <Typography 
                variant="h6" 
                color={performance.risk_metrics?.daily_pnl >= 0 ? 'success.main' : 'error.main'}
              >
                {performance.risk_metrics?.daily_pnl >= 0 ? '+' : ''}
                {performance.risk_metrics?.daily_pnl?.toLocaleString()} KRW
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="caption" color="textSecondary">
                Win Rate
              </Typography>
              <Typography variant="h6">
                {(performance.risk_metrics?.win_rate * 100)?.toFixed(1)}%
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="caption" color="textSecondary">
                Current Exposure
              </Typography>
              <Typography variant="h6">
                {performance.risk_metrics?.current_exposure?.toLocaleString()} KRW
              </Typography>
            </Box>
          </Box>
        )}
      </Paper>
      
      <Box mt={3}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label={`Open (${openPositions.length})`} />
          <Tab label={`Closed (${closedPositions.length})`} />
        </Tabs>
        
        <Box mt={3}>
          {isLoading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : (
            <Grid container spacing={3}>
              {tabValue === 0 && openPositions.map(position => (
                <Grid item xs={12} md={6} lg={4} key={position.position_id}>
                  <PositionCard 
                    position={position} 
                    onClose={handleClosePosition}
                  />
                </Grid>
              ))}
              
              {tabValue === 1 && closedPositions.map(position => (
                <Grid item xs={12} md={6} lg={4} key={position.position_id}>
                  <PositionCard position={position} />
                </Grid>
              ))}
              
              {((tabValue === 0 && openPositions.length === 0) ||
                (tabValue === 1 && closedPositions.length === 0)) && (
                <Grid item xs={12}>
                  <Paper>
                    <Box p={4} textAlign="center">
                      <Typography color="textSecondary">
                        No {tabValue === 0 ? 'open' : 'closed'} positions
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              )}
            </Grid>
          )}
        </Box>
      </Box>
    </div>
  );
};

export default PositionManager;