import { Link } from "react-router-dom";
import type { Algorithm } from "../types/algorithm";
import { CATEGORY_LABELS } from "../constants/categories";
import { MetricsBadge } from "./MetricsBadge";

type AlgorithmCardProps = {
  algorithm: Algorithm;
};

function MetricsBar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 text-gray-500 shrink-0">{label}</span>
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-500 h-2 rounded-full"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-10 text-right text-gray-600">{value.toFixed(2)}</span>
    </div>
  );
}

export function AlgorithmCard({ algorithm }: AlgorithmCardProps) {
  const { id, name, category, libraries, summary_metrics, privacy_risk_level } = algorithm;

  return (
    <Link
      to={`/algorithm/${id}`}
      className="block bg-white rounded-lg shadow hover:shadow-md transition-shadow p-4"
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-800">{name}</h3>
        <span className="inline-block bg-blue-100 text-blue-800 text-xs font-medium px-2 py-0.5 rounded">
          {CATEGORY_LABELS[category]}
        </span>
      </div>

      <div className="flex flex-wrap gap-1 mb-3">
        {libraries.map((lib) => (
          <span
            key={lib}
            className="bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded"
          >
            {lib}
          </span>
        ))}
        {privacy_risk_level && <MetricsBadge level={privacy_risk_level} />}
      </div>

      {summary_metrics && (
        <div className="space-y-1">
          <MetricsBar label="Quality" value={summary_metrics.best_quality_score} max={1} />
          <MetricsBar label="TSTR F1" value={summary_metrics.best_tstr_f1} max={1} />
          <MetricsBar label="DCR" value={summary_metrics.best_dcr_mean} max={1} />
          <MetricsBar
            label="Time(s)"
            value={summary_metrics.fastest_time_sec}
            max={Math.max(summary_metrics.fastest_time_sec, 60)}
          />
        </div>
      )}
    </Link>
  );
}
