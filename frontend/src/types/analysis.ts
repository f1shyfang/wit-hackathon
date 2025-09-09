export interface AnalysisResult {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  results: {
    authenticity_score: number;
    confidence: number;
    summary?: string;
    features: {
      blink_rate: number;
      facial_jitter: number;
      audio_mfcc_variance: number;
    };
  } | null;
  created_at: string;
}

export interface UploadResponse {
  job_id: string;
  status: string;
  message: string;
}
