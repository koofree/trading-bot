import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Grid,
  Slider,
  Switch,
  FormControlLabel,
  Divider,
  Alert
} from '@mui/material';
import { Save, RestartAlt } from '@mui/icons-material';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const Settings = () => {
  const [config, setConfig] = useState({
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
  
  const [apiKeys, setApiKeys] = useState({
    upbit_access_key: '',
    upbit_secret_key: '',
    openai_api_key: ''
  });
  
  const [saving, setSaving] = useState(false);
  
  const handleConfigChange = (key, value) => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };
  
  const handleApiKeyChange = (key, value) => {
    setApiKeys(prev => ({
      ...prev,
      [key]: value
    }));
  };
  
  const handleSaveConfig = async () => {
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
  
  const handleResetDefaults = () => {
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
    <div className="settings">
      <Paper className="settings-header">
        <Typography variant="h5">Settings</Typography>
        <Typography variant="body2" color="textSecondary">
          Configure trading parameters and API keys
        </Typography>
      </Paper>
      
      <Grid container spacing={3} mt={2}>
        <Grid item xs={12} md={6}>
          <Paper className="settings-section">
            <Box p={3}>
              <Typography variant="h6" gutterBottom>
                Trading Parameters
              </Typography>
              
              <Box mt={3}>
                <Typography gutterBottom>
                  Base Position Size: {(config.base_position_size * 100).toFixed(1)}%
                </Typography>
                <Slider
                  value={config.base_position_size}
                  onChange={(e, v) => handleConfigChange('base_position_size', v)}
                  min={0.01}
                  max={0.1}
                  step={0.01}
                  marks
                  valueLabelDisplay="auto"
                  valueLabelFormat={v => `${(v * 100).toFixed(1)}%`}
                />
              </Box>
              
              <Box mt={3}>
                <Typography gutterBottom>
                  Risk Per Trade: {(config.risk_per_trade * 100).toFixed(1)}%
                </Typography>
                <Slider
                  value={config.risk_per_trade}
                  onChange={(e, v) => handleConfigChange('risk_per_trade', v)}
                  min={0.005}
                  max={0.05}
                  step={0.005}
                  marks
                  valueLabelDisplay="auto"
                  valueLabelFormat={v => `${(v * 100).toFixed(1)}%`}
                />
              </Box>
              
              <Box mt={3}>
                <Typography gutterBottom>
                  Max Positions: {config.max_positions}
                </Typography>
                <Slider
                  value={config.max_positions}
                  onChange={(e, v) => handleConfigChange('max_positions', v)}
                  min={1}
                  max={10}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>
              
              <Box mt={3}>
                <Typography gutterBottom>
                  Daily Loss Limit: {(config.daily_loss_limit * 100).toFixed(1)}%
                </Typography>
                <Slider
                  value={config.daily_loss_limit}
                  onChange={(e, v) => handleConfigChange('daily_loss_limit', v)}
                  min={0.01}
                  max={0.2}
                  step={0.01}
                  marks
                  valueLabelDisplay="auto"
                  valueLabelFormat={v => `${(v * 100).toFixed(1)}%`}
                />
              </Box>
              
              <Box mt={3}>
                <Typography gutterBottom>
                  Stop Loss: {(config.stop_loss_percentage * 100).toFixed(1)}%
                </Typography>
                <Slider
                  value={config.stop_loss_percentage}
                  onChange={(e, v) => handleConfigChange('stop_loss_percentage', v)}
                  min={0.01}
                  max={0.1}
                  step={0.01}
                  marks
                  valueLabelDisplay="auto"
                  valueLabelFormat={v => `${(v * 100).toFixed(1)}%`}
                />
              </Box>
              
              <Box mt={3}>
                <Typography gutterBottom>
                  Take Profit: {(config.take_profit_percentage * 100).toFixed(1)}%
                </Typography>
                <Slider
                  value={config.take_profit_percentage}
                  onChange={(e, v) => handleConfigChange('take_profit_percentage', v)}
                  min={0.02}
                  max={0.2}
                  step={0.01}
                  marks
                  valueLabelDisplay="auto"
                  valueLabelFormat={v => `${(v * 100).toFixed(1)}%`}
                />
              </Box>
              
              <Box mt={3}>
                <Typography gutterBottom>
                  Minimum Signal Confidence: {(config.min_confidence * 100).toFixed(0)}%
                </Typography>
                <Slider
                  value={config.min_confidence}
                  onChange={(e, v) => handleConfigChange('min_confidence', v)}
                  min={0.3}
                  max={0.9}
                  step={0.1}
                  marks
                  valueLabelDisplay="auto"
                  valueLabelFormat={v => `${(v * 100).toFixed(0)}%`}
                />
              </Box>
              
              <Box mt={3}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.allow_position_scaling}
                      onChange={(e) => handleConfigChange('allow_position_scaling', e.target.checked)}
                    />
                  }
                  label="Allow Position Scaling"
                />
              </Box>
              
              <Box mt={2}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.allow_short_selling}
                      onChange={(e) => handleConfigChange('allow_short_selling', e.target.checked)}
                    />
                  }
                  label="Allow Short Selling"
                />
              </Box>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper className="settings-section">
            <Box p={3}>
              <Typography variant="h6" gutterBottom>
                API Configuration
              </Typography>
              
              <Alert severity="warning" sx={{ mb: 3 }}>
                API keys are encrypted and stored securely. Never share your keys.
              </Alert>
              
              <TextField
                fullWidth
                label="Upbit Access Key"
                type="password"
                value={apiKeys.upbit_access_key}
                onChange={(e) => handleApiKeyChange('upbit_access_key', e.target.value)}
                margin="normal"
                placeholder="Enter your Upbit access key"
              />
              
              <TextField
                fullWidth
                label="Upbit Secret Key"
                type="password"
                value={apiKeys.upbit_secret_key}
                onChange={(e) => handleApiKeyChange('upbit_secret_key', e.target.value)}
                margin="normal"
                placeholder="Enter your Upbit secret key"
              />
              
              <TextField
                fullWidth
                label="OpenAI API Key"
                type="password"
                value={apiKeys.openai_api_key}
                onChange={(e) => handleApiKeyChange('openai_api_key', e.target.value)}
                margin="normal"
                placeholder="Enter your OpenAI API key"
              />
              
              <Divider sx={{ my: 3 }} />
              
              <Typography variant="h6" gutterBottom>
                Monitored Markets
              </Typography>
              
              <TextField
                fullWidth
                label="Markets (comma-separated)"
                value={config.markets.join(', ')}
                onChange={(e) => handleConfigChange('markets', e.target.value.split(',').map(m => m.trim()))}
                margin="normal"
                placeholder="KRW-BTC, KRW-ETH, KRW-XRP"
                helperText="Enter market pairs separated by commas"
              />
            </Box>
          </Paper>
          
          <Box mt={3} display="flex" gap={2}>
            <Button
              variant="contained"
              startIcon={<Save />}
              onClick={handleSaveConfig}
              disabled={saving}
              fullWidth
            >
              Save Configuration
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<RestartAlt />}
              onClick={handleResetDefaults}
              fullWidth
            >
              Reset to Defaults
            </Button>
          </Box>
        </Grid>
      </Grid>
    </div>
  );
};

export default Settings;