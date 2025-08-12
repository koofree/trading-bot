import React, { useState, useRef } from 'react';
import {
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip
} from '@mui/material';
import { CloudUpload, Description, Analytics } from '@mui/icons-material';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const MarketAnalysis = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const fileInputRef = useRef(null);
  
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    setUploading(true);
    
    try {
      const response = await axios.post(`${API_URL}/api/upload-report`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data.status === 'success') {
        toast.success('Report uploaded and analyzed successfully');
        setUploadedFiles(prev => [...prev, {
          filename: file.name,
          analysis: response.data.analysis,
          timestamp: new Date().toISOString()
        }]);
        setAnalysis(response.data.analysis);
      } else {
        toast.error('Failed to analyze report');
      }
    } catch (error) {
      toast.error('Error uploading file');
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };
  
  const renderExtractedData = (data) => {
    if (!data) return null;
    
    return (
      <Box>
        {data.prices && data.prices.length > 0 && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Extracted Prices
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              {data.prices.slice(0, 5).map((price, idx) => (
                <Chip key={idx} label={`${price.toLocaleString()} KRW`} size="small" />
              ))}
            </Box>
          </Box>
        )}
        
        {data.tickers && data.tickers.length > 0 && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Mentioned Tickers
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              {data.tickers.map((ticker, idx) => (
                <Chip key={idx} label={ticker} color="primary" size="small" />
              ))}
            </Box>
          </Box>
        )}
        
        {data.keywords && Object.keys(data.keywords).length > 0 && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Key Terms
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              {Object.entries(data.keywords).slice(0, 8).map(([word, count]) => (
                <Chip 
                  key={word} 
                  label={`${word} (${count})`} 
                  variant="outlined" 
                  size="small"
                />
              ))}
            </Box>
          </Box>
        )}
      </Box>
    );
  };
  
  const renderLLMAnalysis = (llmAnalysis) => {
    if (!llmAnalysis) return null;
    
    return (
      <Box>
        {llmAnalysis.price_targets && llmAnalysis.price_targets.length > 0 && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Price Targets
            </Typography>
            {llmAnalysis.price_targets.map((target, idx) => (
              <Typography key={idx} variant="body2" color="textSecondary">
                • {target}
              </Typography>
            ))}
          </Box>
        )}
        
        {llmAnalysis.trends && llmAnalysis.trends.length > 0 && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Market Trends
            </Typography>
            {llmAnalysis.trends.map((trend, idx) => (
              <Typography key={idx} variant="body2" color="textSecondary">
                • {trend}
              </Typography>
            ))}
          </Box>
        )}
        
        {llmAnalysis.recommendations && llmAnalysis.recommendations.length > 0 && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Recommendations
            </Typography>
            {llmAnalysis.recommendations.map((rec, idx) => (
              <Typography key={idx} variant="body2" color="textSecondary">
                • {rec}
              </Typography>
            ))}
          </Box>
        )}
        
        {llmAnalysis.summary && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Summary
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {llmAnalysis.summary}
            </Typography>
          </Box>
        )}
      </Box>
    );
  };
  
  return (
    <div className="market-analysis">
      <Paper className="analysis-header">
        <Typography variant="h5">Market Analysis</Typography>
        <Typography variant="body2" color="textSecondary">
          Upload reports and documents for AI-powered market analysis
        </Typography>
      </Paper>
      
      <Grid container spacing={3} mt={2}>
        <Grid item xs={12} md={4}>
          <Paper className="upload-section">
            <Box p={3}>
              <Typography variant="h6" gutterBottom>
                Upload Report
              </Typography>
              
              <Box
                className="upload-dropzone"
                onClick={() => fileInputRef.current?.click()}
                sx={{
                  border: '2px dashed #ccc',
                  borderRadius: 2,
                  p: 4,
                  textAlign: 'center',
                  cursor: 'pointer',
                  '&:hover': {
                    borderColor: 'primary.main',
                    bgcolor: 'action.hover'
                  }
                }}
              >
                <CloudUpload fontSize="large" color="action" />
                <Typography variant="body1" mt={2}>
                  Click to upload report
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  PDF, DOCX, TXT, CSV, XLSX supported
                </Typography>
              </Box>
              
              <input
                ref={fileInputRef}
                type="file"
                hidden
                accept=".pdf,.docx,.txt,.csv,.xlsx"
                onChange={handleFileUpload}
              />
              
              {uploading && <LinearProgress sx={{ mt: 2 }} />}
              
              {uploadedFiles.length > 0 && (
                <Box mt={3}>
                  <Typography variant="subtitle2" gutterBottom>
                    Uploaded Files
                  </Typography>
                  {uploadedFiles.map((file, idx) => (
                    <Box key={idx} display="flex" alignItems="center" gap={1} mb={1}>
                      <Description fontSize="small" />
                      <Typography variant="body2" noWrap>
                        {file.filename}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={8}>
          {analysis ? (
            <Paper className="analysis-results">
              <Box p={3}>
                <Typography variant="h6" gutterBottom>
                  Analysis Results
                </Typography>
                
                {analysis.extracted_data && (
                  <Card sx={{ mb: 2 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Extracted Information
                      </Typography>
                      {renderExtractedData(analysis.extracted_data)}
                    </CardContent>
                  </Card>
                )}
                
                {analysis.llm_analysis && (
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        AI Analysis
                      </Typography>
                      {renderLLMAnalysis(analysis.llm_analysis)}
                    </CardContent>
                  </Card>
                )}
              </Box>
            </Paper>
          ) : (
            <Paper>
              <Box p={4} textAlign="center">
                <Analytics fontSize="large" color="action" />
                <Typography variant="body1" mt={2} color="textSecondary">
                  Upload a report to see analysis results
                </Typography>
              </Box>
            </Paper>
          )}
        </Grid>
      </Grid>
    </div>
  );
};

export default MarketAnalysis;