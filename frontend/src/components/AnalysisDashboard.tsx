'use client';

import { useState, useEffect } from 'react';
import { RefreshCw, Eye, AlertTriangle, CheckCircle } from 'lucide-react';
import { AnalysisResult } from '@/types/analysis';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import axios from 'axios';

interface AnalysisDashboardProps {
  result: AnalysisResult;
  onNewAnalysis: () => void;
}

export default function AnalysisDashboard({ result, onNewAnalysis }: AnalysisDashboardProps) {
  const [currentResult, setCurrentResult] = useState<AnalysisResult>(result);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    setCurrentResult(result);
  }, [result]);

  const refreshResults = async () => {
    if (!currentResult.job_id) return;
    
    setIsRefreshing(true);
    try {
      const response = await axios.get(`http://localhost:52513/api/results/${currentResult.job_id}`);
      setCurrentResult(response.data);
    } catch (error) {
      console.error('Failed to refresh results:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const getAuthenticityColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getAuthenticityBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getAuthenticityIcon = (score: number) => {
    if (score >= 80) return <CheckCircle className="w-6 h-6 text-green-600" />;
    if (score >= 60) return <AlertTriangle className="w-6 h-6 text-yellow-600" />;
    return <AlertTriangle className="w-6 h-6 text-red-600" />;
  };

  const getAuthenticityLabel = (score: number) => {
    if (score >= 80) return 'Likely Authentic';
    if (score >= 60) return 'Suspicious';
    return 'Likely Deepfake';
  };

  if (!currentResult.results) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto mb-4"></div>
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          Analysis in Progress...
        </h2>
        <p className="text-gray-600">
          Please wait while we analyze your video.
        </p>
      </div>
    );
  }

  const { authenticity_score, confidence, features, summary } = currentResult.results as NonNullable<AnalysisResult['results']>;

  // Prepare data for charts
  const featureData = [
    { name: 'Blink Rate', value: features.blink_rate, unit: 'blinks/min' },
    { name: 'Facial Jitter', value: features.facial_jitter, unit: 'variance' },
    { name: 'Audio MFCC', value: features.audio_mfcc_variance, unit: 'variance' },
  ];

  const pieData = [
    { name: 'Authentic', value: authenticity_score, color: '#10B981' },
    { name: 'Deepfake', value: 100 - authenticity_score, color: '#EF4444' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Analysis Results</h2>
          <p className="text-gray-600 mt-1">
            Job ID: {currentResult.job_id}
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={refreshResults}
            disabled={isRefreshing}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={onNewAnalysis}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <Eye className="w-4 h-4 mr-2" />
            New Analysis
          </button>
        </div>
      </div>

      {/* Authenticity Score Card */}
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="text-center">
          <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full ${getAuthenticityBgColor(authenticity_score)} mb-4`}>
            {getAuthenticityIcon(authenticity_score)}
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            {authenticity_score.toFixed(1)}% Authentic
          </h3>
          <p className={`text-lg font-semibold ${getAuthenticityColor(authenticity_score)} mb-2`}>
            {getAuthenticityLabel(authenticity_score)}
          </p>
          <p className="text-gray-600">
            Confidence: {(confidence * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Summary Box */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Summary</h3>
        <p className="text-gray-700">
          {authenticity_score >= 80
            ? 'This appears to be a real video.'
            : (summary || 'Potential deepfake indicators present.')}
        </p>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Feature Analysis Chart */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Feature Analysis</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={featureData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip 
                formatter={(value: number, name: string, item: { payload?: { unit?: string } }) => [
                  `${value.toFixed(3)} ${item.payload?.unit ?? ''}`,
                  name
                ]}
              />
              <Bar dataKey="value" fill="#6366F1" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Authenticity Distribution */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Authenticity Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Features Table */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Detailed Feature Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Feature
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Interpretation
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Blink Rate
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {features.blink_rate.toFixed(2)} blinks/min
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {features.blink_rate > 15 ? 'Normal range' : 'Below normal - potential deepfake indicator'}
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Facial Jitter
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {features.facial_jitter.toFixed(3)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {features.facial_jitter < 0.2 ? 'Stable - authentic' : 'High variance - suspicious'}
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Audio MFCC Variance
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {features.audio_mfcc_variance.toFixed(3)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {features.audio_mfcc_variance < 0.3 ? 'Natural audio patterns' : 'Synthetic audio detected'}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Analysis Metadata */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Analysis Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
          <div>
            <span className="font-medium">Analysis Date:</span> {new Date(currentResult.created_at).toLocaleString()}
          </div>
          <div>
            <span className="font-medium">Status:</span> {currentResult.status}
          </div>
          <div>
            <span className="font-medium">Model Confidence:</span> {(confidence * 100).toFixed(1)}%
          </div>
          <div>
            <span className="font-medium">Processing Time:</span> ~2-5 seconds
          </div>
        </div>
      </div>
    </div>
  );
}
