import axios from 'axios';
import type React from 'react';
import { useRef, useState } from 'react';
import toast from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface UploadedFile {
  filename: string;
  analysis: AnalysisResult;
  timestamp: string;
}

interface ExtractedData {
  prices?: number[];
  tickers?: string[];
  keywords?: Record<string, number>;
}

interface LLMAnalysis {
  price_targets?: string[];
  trends?: string[];
  recommendations?: string[];
  summary?: string;
}

interface AnalysisResult {
  extracted_data?: ExtractedData;
  llm_analysis?: LLMAnalysis;
}

interface ApiResponse {
  status: string;
  analysis: AnalysisResult;
}

const MarketAnalysis: React.FC = () => {
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);

    try {
      const response = await axios.post<ApiResponse>(`${API_URL}/api/upload-report`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.status === 'success') {
        toast.success('Report uploaded and analyzed successfully');
        setUploadedFiles((prev) => [
          ...prev,
          {
            filename: file.name,
            analysis: response.data.analysis,
            timestamp: new Date().toISOString(),
          },
        ]);
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

  const renderExtractedData = (data: ExtractedData): React.ReactElement | null => {
    if (!data) return null;

    return (
      <div>
        {data.prices && data.prices.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Extracted Prices</h4>
            <div className="flex flex-wrap gap-2">
              {data.prices.slice(0, 5).map((price: number, idx: number) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                >
                  {price.toLocaleString()} KRW
                </span>
              ))}
            </div>
          </div>
        )}

        {data.tickers && data.tickers.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Mentioned Tickers</h4>
            <div className="flex flex-wrap gap-2">
              {data.tickers.map((ticker: string, idx: number) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                >
                  {ticker}
                </span>
              ))}
            </div>
          </div>
        )}

        {data.keywords && Object.keys(data.keywords).length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Key Terms</h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(data.keywords)
                .slice(0, 8)
                .map(([word, count]: [string, number]) => (
                  <span
                    key={word}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-50 text-gray-700 border border-gray-200"
                  >
                    {word} ({count})
                  </span>
                ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderLLMAnalysis = (llmAnalysis: LLMAnalysis): React.ReactElement | null => {
    if (!llmAnalysis) return null;

    return (
      <div>
        {llmAnalysis.price_targets && llmAnalysis.price_targets.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Price Targets</h4>
            <div className="space-y-1">
              {llmAnalysis.price_targets.map((target: string, idx: number) => (
                <p key={idx} className="text-sm text-gray-600">
                  • {target}
                </p>
              ))}
            </div>
          </div>
        )}

        {llmAnalysis.trends && llmAnalysis.trends.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Market Trends</h4>
            <div className="space-y-1">
              {llmAnalysis.trends.map((trend: string, idx: number) => (
                <p key={idx} className="text-sm text-gray-600">
                  • {trend}
                </p>
              ))}
            </div>
          </div>
        )}

        {llmAnalysis.recommendations && llmAnalysis.recommendations.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Recommendations</h4>
            <div className="space-y-1">
              {llmAnalysis.recommendations.map((rec: string, idx: number) => (
                <p key={idx} className="text-sm text-gray-600">
                  • {rec}
                </p>
              ))}
            </div>
          </div>
        )}

        {llmAnalysis.summary && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Summary</h4>
            <p className="text-sm text-gray-600">{llmAnalysis.summary}</p>
          </div>
        )}
      </div>
    );
  };

  const handleUploadClick = (): void => {
    fileInputRef.current?.click();
  };

  return (
    <div>
      <div className="mb-6 bg-white p-6 rounded-xl shadow-sm">
        <h1 className="text-2xl font-bold text-gray-800">Market Analysis</h1>
        <p className="text-sm text-gray-500 mt-1">
          Upload reports and documents for AI-powered market analysis
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Upload Report</h2>

            <div
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer transition-all hover:border-indigo-400 hover:bg-gray-50"
              onClick={handleUploadClick}
            >
              <svg
                className="w-12 h-12 text-gray-400 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p className="text-base font-medium text-gray-700 mb-2">Click to upload report</p>
              <p className="text-xs text-gray-500">PDF, DOCX, TXT, CSV, XLSX supported</p>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              hidden
              accept=".pdf,.docx,.txt,.csv,.xlsx"
              onChange={handleFileUpload}
            />

            {uploading && (
              <div className="mt-4">
                <div className="bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-indigo-500 h-2 rounded-full animate-pulse"
                    style={{ width: '100%' }}
                  ></div>
                </div>
              </div>
            )}

            {uploadedFiles.length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Uploaded Files</h3>
                <div className="space-y-2">
                  {uploadedFiles.map((file: UploadedFile, idx: number) => (
                    <div key={idx} className="flex items-center gap-2 text-sm">
                      <svg
                        className="w-4 h-4 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      <span className="text-gray-700 truncate">{file.filename}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-2">
          {analysis ? (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-6">Analysis Results</h2>

              {analysis.extracted_data && (
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <h3 className="text-base font-semibold text-gray-800 mb-4">
                    Extracted Information
                  </h3>
                  {renderExtractedData(analysis.extracted_data)}
                </div>
              )}

              {analysis.llm_analysis && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-base font-semibold text-gray-800 mb-4">AI Analysis</h3>
                  {renderLLMAnalysis(analysis.llm_analysis)}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm">
              <div className="p-8 text-center">
                <svg
                  className="w-16 h-16 text-gray-300 mx-auto mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
                <p className="text-base text-gray-500">Upload a report to see analysis results</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MarketAnalysis;
