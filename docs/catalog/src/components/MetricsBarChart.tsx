import { useMemo } from "react";
import type { CaseResult } from "../types/experiment-case";

type Props = {
  results: CaseResult[];
};

type MetricDef = {
  key: "quality_score" | "tstr_f1" | "dcr_mean";
  label: string;
  color: string;
  bgColor: string;
};

const METRICS: MetricDef[] = [
  { key: "quality_score", label: "Quality Score", color: "bg-blue-500", bgColor: "bg-blue-100" },
  { key: "tstr_f1", label: "TSTR F1", color: "bg-emerald-500", bgColor: "bg-emerald-100" },
  { key: "dcr_mean", label: "DCR Mean", color: "bg-amber-500", bgColor: "bg-amber-100" },
];

export function MetricsBarChart({ results }: Props) {
  const maxValue = useMemo(() => {
    let max = 0;
    for (const r of results) {
      for (const m of METRICS) {
        const v = r.metrics[m.key];
        if (v != null && v > max) max = v;
      }
    }
    return Math.max(max, 1);
  }, [results]);

  const activeMetrics = useMemo(() => {
    return METRICS.filter((m) => results.some((r) => r.metrics[m.key] != null));
  }, [results]);

  if (activeMetrics.length === 0) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
        精度比較
      </h2>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mb-4">
        {activeMetrics.map((m) => (
          <div key={m.key} className="flex items-center gap-1.5 text-xs text-gray-600">
            <span className={`inline-block w-3 h-3 rounded-sm ${m.color}`} />
            {m.label}
          </div>
        ))}
      </div>

      {/* Bars */}
      <div className="space-y-4">
        {results.map((r, idx) => (
          <div key={`${r.algorithm_id}-${r.library}-${idx}`}>
            <div className="text-sm font-medium text-gray-700 mb-1.5">
              {r.algorithm_name}
              <span className="text-gray-400 text-xs ml-1">({r.library})</span>
            </div>
            <div className="space-y-1">
              {activeMetrics.map((m) => {
                const value = r.metrics[m.key];
                const pct = value != null ? (value / maxValue) * 100 : 0;
                return (
                  <div key={m.key} className="flex items-center gap-2">
                    <div className="w-20 text-xs text-gray-400 text-right shrink-0">{m.label}</div>
                    <div className={`flex-1 h-5 rounded ${m.bgColor} overflow-hidden`}>
                      {value != null && (
                        <div
                          className={`h-full rounded ${m.color} transition-all duration-500`}
                          style={{ width: `${Math.max(pct, 2)}%` }}
                        />
                      )}
                    </div>
                    <div className="w-14 text-xs font-mono text-gray-600 text-right shrink-0">
                      {value != null ? value.toFixed(3) : "—"}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-400 mt-4">
        Quality Score・TSTR F1 は高いほど品質が良い。DCR Mean は高いほどプライバシー保護が強い。
      </p>
    </div>
  );
}
