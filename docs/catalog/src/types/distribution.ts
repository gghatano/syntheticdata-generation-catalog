export type NumericBin = {
  /** bin の左端（包含） */
  x: number;
  /** bin の右端（排他、最終 bin のみ包含） */
  x_end: number;
  /** real の度数（出現件数） */
  real: number;
  /** synth の度数 */
  synth: number;
};

export type CategoryBar = {
  name: string;
  /** real の出現比率 (0-1) */
  real_pct: number;
  /** synth の出現比率 (0-1) */
  synth_pct: number;
  /** real の生件数 */
  real_count: number;
  /** synth の生件数 */
  synth_count: number;
};

export type NumericDistributionItem = {
  type: "numeric";
  column: string;
  label: string;
  unit?: string;
  real_mean: number;
  synth_mean: number;
  real_std: number;
  synth_std: number;
  bins: NumericBin[];
};

export type CategoricalDistributionItem = {
  type: "categorical";
  column: string;
  label: string;
  /** real / synth 合算で頻度上位 N 件のみ表示。"その他" にまとめた場合は他の説明を含める */
  categories: CategoryBar[];
  total_categories?: number;
};

export type DistributionItem = NumericDistributionItem | CategoricalDistributionItem;

export type DistributionData = {
  case_id: string;
  /** 比較対象の合成手法（experiment-cases.json の results にある algorithm_id を想定） */
  selected_synth: {
    algorithm: string;
    library: string;
    csv: string;
  };
  /** real CSV のソース */
  real_source: {
    csv: string;
    rows: number;
  };
  /** 比較対象の synth CSV のメタ */
  synth_source: {
    rows: number;
  };
  items: DistributionItem[];
  note: string;
};
