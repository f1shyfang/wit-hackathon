'use client';

import { useState } from 'react';
import FileUpload from '@/components/FileUpload';
import AnalysisDashboard from '@/components/AnalysisDashboard';
import { AnalysisResult } from '@/types/analysis';

export default function Home() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAnalysisComplete = (result: AnalysisResult) => {
    setAnalysisResult(result);
    setIsAnalyzing(false);
  };

  const handleAnalysisStart = () => {
    setIsAnalyzing(true);
    setAnalysisResult(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            NotReal.ly
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Advanced deepfake detection powered by multi-modal AI analysis. 
            Upload a video to get an authenticity score and detailed analysis.
          </p>
        </div>

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          {!analysisResult && !isAnalyzing && (
            <FileUpload onAnalysisStart={handleAnalysisStart} onAnalysisComplete={handleAnalysisComplete} />
          )}
          
          {isAnalyzing && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto mb-4"></div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Analyzing Video...
              </h2>
              <p className="text-gray-600">
                Our AI is examining facial features, audio patterns, and other indicators.
                This may take a few moments.
              </p>
            </div>
          )}
          
          {analysisResult && (
            <AnalysisDashboard 
              result={analysisResult} 
              onNewAnalysis={() => {
                setAnalysisResult(null);
                setIsAnalyzing(false);
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
}