export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface HealthStatus {
  app: string;
  model_loaded: boolean;
  scaler_loaded?: boolean;
  model_path?: string;
  model_type: string;
  matlab_engine_available: boolean | null;
  matlab_shared_engines: string[] | null;
  llm_enabled: boolean;
  llm_configured: boolean;
  llm_provider?: string;
  llm_model?: string | null;
  rag_enabled: boolean;
}

export type LabelMap = Record<string, string>;

export type FeatureList = string[];

export interface DatasetSummary {
  total_rows?: number;
  total_columns?: number;
  validation_mode?: string;
  has_label?: boolean;
  label_distribution?: Record<string, number>;
  [key: string]: unknown;
}

export interface RowPrediction {
  row_index: number;
  predicted_label: string;
  fault_name: string;
  confidence?: number | null;
}

export interface ModelResult {
  total_rows: number;
  dominant_label: string;
  dominant_fault_name: string;
  dominant_ratio: number;
  avg_confidence?: number | null;
  severity: string;
  prediction_distribution: Record<string, number>;
  row_predictions_preview?: RowPrediction[];
}

export interface DiagnosisUploadResponse {
  diagnosis_id: number;
  dataset_summary: DatasetSummary;
  model_result: ModelResult;
  explanation: string;
  maintenance_suggestions: string[];
}

export interface ChatRequest {
  diagnosis_id: number;
  question: string;
}

export interface ChatResponse {
  answer: string;
  sources?: string[];
}

export type ReportFormat = 'md' | 'html' | 'docx';

export interface ReportResponse {
  report_path: string;
  report_filename?: string;
  report_format?: ReportFormat;
  download_url?: string;
  report_content?: string;
}

export interface ApiErrorPayload {
  code: number;
  message: string;
  data?: unknown;
  status?: number;
}
