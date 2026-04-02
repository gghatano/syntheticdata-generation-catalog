import { Link } from "react-router-dom";
import type { Algorithm } from "../types/algorithm";
import { CATEGORY_LABELS, DATA_TYPE_LABELS } from "../constants/categories";
import { MetricsBadge } from "./MetricsBadge";

type AlgorithmCardProps = {
  algorithm: Algorithm;
};

function MetricsBar({ label, value, max, color }: { label: string; value: number; max: number; color?: string }) {
  const pct = Math.min((value / max) * 100, 100);
  const barColor = color ?? "bg-blue-500";
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-20 text-gray-500 shrink-0 font-medium">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-2.5 overflow-hidden">
        <div
          className={`${barColor} h-2.5 rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-12 text-right text-gray-600 font-mono tabular-nums">{(value * 100).toFixed(0)}%</span>
    </div>
  );
}

export function AlgorithmCard({ algorithm }: AlgorithmCardProps) {
  const { id, name, category, libraries, supported_data, summary_metrics, privacy_risk_level } = algorithm;

  return (
    <Link
      to={`/algorithm/${id}`}
      className="block bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 p-5 border border-gray-100 hover:border-gray-200"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-bold text-gray-800">{name}</h3>
        <span className="inline-block bg-blue-50 text-blue-700 text-xs font-semibold px-2.5 py-1 rounded-full">
          {CATEGORY_LABELS[category]}
        </span>
      </div>

      {/* Privacy risk badge */}
      {privacy_risk_level && (
        <div className="mb-3">
          <MetricsBadge level={privacy_risk_level} />
        </div>
      )}

      {/* Data type badges */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {supported_data.map((dt) => (
          <span
            key={dt}
            className="inline-flex items-center bg-indigo-50 text-indigo-700 text-xs font-medium px-2 py-0.5 rounded-full"
          >
            {DATA_TYPE_LABELS[dt]}
          </span>
        ))}
      </div>

      {/* Metrics mini bar chart */}
      {summary_metrics && (
        <div className="space-y-1.5 mb-4">
          {summary_metrics.best_quality_score != null && (
            <MetricsBar
              label="Quality"
              value={summary_metrics.best_quality_score}
              max={1}
              color="bg-emerald-500"
            />
          )}
          {summary_metrics.best_tstr_f1 != null && (
            <MetricsBar
              label="TSTR F1"
              value={summary_metrics.best_tstr_f1}
              max={1}
              color="bg-sky-500"
            />
          )}
        </div>
      )}

      {/* Library badges */}
      <div className="flex flex-wrap gap-1.5 pt-3 border-t border-gray-100">
        {libraries.map((lib) => (
          <span
            key={lib}
            className="bg-gray-50 text-gray-600 text-xs font-medium px-2.5 py-1 rounded-full border border-gray-200"
          >
            {lib}
          </span>
        ))}
      </div>
    </Link>
  );
}
