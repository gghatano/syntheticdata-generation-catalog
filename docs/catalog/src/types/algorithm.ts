export type AlgorithmCategory = "gan" | "vae" | "copula" | "bayesian" | "flow" | "sequential";
export type DataType = "single_table" | "multi_table" | "timeseries";
export type PrivacyRiskLevel = "low" | "medium" | "high";

export type Algorithm = {
  id: string;
  name: string;
  libraries: string[];
  category: AlgorithmCategory;
  supported_data: DataType[];
  tags: string[];
  use_cases: string[];
  input_requirements: string[];
  privacy_mechanism?: string;
  privacy_risk_level?: PrivacyRiskLevel;
  description: string;
  strengths: string[];
  weaknesses: string[];
  reference?: string;
  experiments: Experiment[];
  summary_metrics?: SummaryMetrics;
};

export type Experiment = {
  id: string;
  library: string;
  library_version?: string;
  params: Record<string, unknown>;
  dataset: string;
  data_type: DataType;
  phase: string;
  metrics: {
    quality_score?: number;
    diagnostic_score?: number;
    tstr_accuracy?: number;
    tstr_f1?: number;
    dcr_mean?: number;
    dcr_5th_percentile?: number;
    exact_match_rate?: number;
    time_sec?: number;
  };
};

export type SummaryMetrics = {
  best_quality_score: number;
  best_tstr_f1: number;
  best_dcr_mean: number;
  fastest_time_sec: number;
};
