export type DataCategory =
  | "single_table_master"
  | "single_table_transaction"
  | "single_table_timeseries"
  | "multi_table";

export const DATA_CATEGORY_LABELS: Record<DataCategory, string> = {
  single_table_master: "単一表（マスタ）",
  single_table_transaction: "単一表（トランザクション）",
  single_table_timeseries: "単一表（時系列）",
  multi_table: "複数表",
};

export const DATA_CATEGORY_ICONS: Record<DataCategory, string> = {
  single_table_master: "\uD83D\uDCCA",
  single_table_transaction: "\uD83D\uDCCB",
  single_table_timeseries: "\uD83D\uDCC8",
  multi_table: "\uD83D\uDD17",
};

export type ScriptRole = "prepare" | "synthesize" | "evaluate";

export type CaseScript = {
  role: ScriptRole;
  library: string;
  path: string;
  description?: string;
};

export const SCRIPT_ROLE_LABELS: Record<ScriptRole, string> = {
  prepare: "データ準備",
  synthesize: "合成",
  evaluate: "評価",
};

export type ExperimentCase = {
  id: string;
  title: string;
  data_category: DataCategory;
  scenario: {
    description: string;
    use_case: string;
  };
  dataset: {
    name: string;
    source_url?: string;
    rows: number;
    columns: number;
    features: string[];
  };
  results: CaseResult[];
  recommendation: string;
  scripts?: CaseScript[];
};

export type CaseResult = {
  algorithm_id: string;
  algorithm_name: string;
  library: string;
  params: Record<string, unknown>;
  metrics: {
    quality_score?: number;
    tstr_accuracy?: number;
    tstr_f1?: number;
    dcr_mean?: number;
    time_sec?: number;
  };
  privacy_risk: "low" | "medium" | "high" | null;
};
