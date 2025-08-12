import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Box, Chip } from '@mui/material';
import { 
  Dashboard, 
  ShowChart, 
  AccountBalance, 
  Analytics, 
  Settings,
  FiberManualRecord
} from '@mui/icons-material';
import { useWebSocketContext } from '../contexts/WebSocketContext';

const Navigation = () => {
  const location = useLocation();
  const { connected } = useWebSocketContext();
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: <Dashboard /> },
    { path: '/signals', label: 'Signals', icon: <ShowChart /> },
    { path: '/positions', label: 'Positions', icon: <AccountBalance /> },
    { path: '/analysis', label: 'Analysis', icon: <Analytics /> },
    { path: '/settings', label: 'Settings', icon: <Settings /> }
  ];
  
  return (
    <AppBar position="static" className="navigation">
      <Toolbar>
        <Typography variant="h6" className="nav-title">
          Trading Bot
        </Typography>
        
        <Box className="nav-links">
          {navItems.map(item => (
            <Button
              key={item.path}
              component={Link}
              to={item.path}
              startIcon={item.icon}
              className={location.pathname === item.path ? 'active' : ''}
            >
              {item.label}
            </Button>
          ))}
        </Box>
        
        <Box className="connection-status">
          <Chip
            icon={<FiberManualRecord />}
            label={connected ? 'Connected' : 'Disconnected'}
            color={connected ? 'success' : 'error'}
            size="small"
          />
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation;