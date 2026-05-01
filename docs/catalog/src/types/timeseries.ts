export type TimeSeriesPoint = {
  x: number;
  real: number | null;
  synth: number | null;
};

export type TimeSeriesSeries = {
  name: string;
  label: string;
  unit: string;
  real_mean: number;
  synth_mean: number;
  real_std: number;
  synth_std: number;
  points: TimeSeriesPoint[];
};

export type TimeSeriesPair = {
  /** 例: "中型株 (AAPL)" */
  label: string;
  /** real CSV 内の sequence_key 値（例: "AAPL", "US, New York"） */
  real_id: string;
  /** synth CSV 内の sequence_key 値（例: "AAAJ"） */
  synth_id: string;
  /** real / synth 平均値の差（マッチング選定の根拠表示用、任意） */
  match_reason?: string;
  date_range_real: {
    start: string;
    end: string;
  };
  sequence_length: number;
  series: TimeSeriesSeries[];
};

export type AggregateBin = {
  x: number;
  x_end: number;
  real: number;
  synth: number;
};

export type AggregateSeries = {
  name: string;
  label: string;
  unit: string;
  /** real 全シーケンスを合算した値域からの度数 */
  real_count: number;
  synth_count: number;
  real_mean: number;
  synth_mean: number;
  real_std: number;
  synth_std: number;
  bins: AggregateBin[];
};

export type TimeSeriesData = {
  case_id: string;
  pairs: TimeSeriesPair[];
  /** 全シーケンス合算の分布比較。pair 単位の比較が当てにならない場合の補完 */
  aggregate?: {
    /** 説明文 */
    note?: string;
    series: AggregateSeries[];
  };
  note: string;
  source?: {
    real_csv_sha256_prefix: string;
    synth_csv_sha256_prefix: string;
  };
};
