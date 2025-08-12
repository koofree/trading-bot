import React from 'react';
import { Card, CardContent, Typography, Box, Chip, Button } from '@mui/material';
import { ArrowUpward, ArrowDownward } from '@mui/icons-material';

const PositionCard = ({ position, onClose }) => {
  const pnlColor = position.pnl >= 0 ? '#4caf50' : '#f44336';
  const pnlIcon = position.pnl >= 0 ? <ArrowUpward /> : <ArrowDownward />;
  
  const formatDateTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };
  
  return (
    <Card className="position-card">
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">{position.market}</Typography>
          <Chip 
            label={position.status}
            color={position.status === 'OPEN' ? 'primary' : 'default'}
            size="small"
          />
        </Box>
        
        <Box display="grid" gridTemplateColumns="1fr 1fr" gap={1} mb={2}>
          <Box>
            <Typography variant="caption" color="textSecondary">
              Entry Price
            </Typography>
            <Typography variant="body2">
              {position.entry_price?.toLocaleString()} KRW
            </Typography>
          </Box>
          
          <Box>
            <Typography variant="caption" color="textSecondary">
              Current Price
            </Typography>
            <Typography variant="body2">
              {position.current_price?.toLocaleString()} KRW
            </Typography>
          </Box>
          
          <Box>
            <Typography variant="caption" color="textSecondary">
              Volume
            </Typography>
            <Typography variant="body2">
              {position.volume?.toFixed(4)}
            </Typography>
          </Box>
          
          <Box>
            <Typography variant="caption" color="textSecondary">
              Filled
            </Typography>
            <Typography variant="body2">
              {position.filled_volume?.toFixed(4)}
            </Typography>
          </Box>
        </Box>
        
        <Box 
          display="flex" 
          alignItems="center" 
          gap={1} 
          p={1} 
          bgcolor={pnlColor + '20'}
          borderRadius={1}
          mb={2}
        >
          <Box display="flex" alignItems="center" style={{ color: pnlColor }}>
            {pnlIcon}
          </Box>
          <Box flex={1}>
            <Typography variant="caption" color="textSecondary">
              P&L
            </Typography>
            <Typography variant="body2" style={{ color: pnlColor }}>
              {position.pnl >= 0 ? '+' : ''}{position.pnl?.toLocaleString()} KRW
              ({position.pnl_percentage >= 0 ? '+' : ''}{position.pnl_percentage?.toFixed(2)}%)
            </Typography>
          </Box>
        </Box>
        
        {position.stop_loss && (
          <Box mb={1}>
            <Typography variant="caption" color="textSecondary">
              Stop Loss: {position.stop_loss?.toLocaleString()} KRW
            </Typography>
          </Box>
        )}
        
        {position.take_profit && (
          <Box mb={1}>
            <Typography variant="caption" color="textSecondary">
              Take Profit: {position.take_profit?.toLocaleString()} KRW
            </Typography>
          </Box>
        )}
        
        <Typography variant="caption" color="textSecondary">
          Opened: {formatDateTime(position.opened_at)}
        </Typography>
        
        {position.status === 'OPEN' && onClose && (
          <Box mt={2}>
            <Button 
              variant="outlined" 
              color="error" 
              size="small" 
              fullWidth
              onClick={() => onClose(position)}
            >
              Close Position
            </Button>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default PositionCard;