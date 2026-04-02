import type { AlgorithmCategory, DataType, PrivacyRiskLevel } from "../types/algorithm";

export const CATEGORY_LABELS: Record<AlgorithmCategory, string> = {
  gan: "GAN",
  vae: "VAE",
  copula: "コピュラ",
  bayesian: "ベイジアン",
  flow: "正規化フロー",
  sequential: "時系列モデル",
};

export const DATA_TYPE_LABELS: Record<DataType, string> = {
  single_table: "単一表",
  multi_table: "複数表",
  timeseries: "時系列",
};

export const PRIVACY_RISK_LABELS: Record<PrivacyRiskLevel, { label: string; color: string }> = {
  low: { label: "低リスク", color: "green" },
  medium: { label: "中リスク", color: "yellow" },
  high: { label: "高リスク", color: "red" },
};
