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

export type TimeSeriesData = {
  case_id: string;
  selected_real_location: string;
  selected_synth_sequence: string;
  date_range_real: {
    start: string;
    end: string;
  };
  sequence_length: number;
  series: TimeSeriesSeries[];
  note: string;
  source?: {
    real_csv_sha256_prefix: string;
    synth_csv_sha256_prefix: string;
  };
};
