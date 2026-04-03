import { Link } from "react-router-dom";
import type { ExperimentCase, CaseResult } from "../types/experiment-case";
import { DATA_CATEGORY_LABELS, DATA_CATEGORY_ICONS } from "../types/experiment-case";

const PRIVACY_BADGE: Record<string, { label: string; bg: string; text: string }> = {
  low: { label: "低", bg: "bg-green-100", text: "text-green-700" },
  medium: { label: "中", bg: "bg-yellow-100", text: "text-yellow-700" },
  high: { label: "高", bg: "bg-red-100", text: "text-red-700" },
};

function formatTime(sec: number): string {
  if (sec < 60) return `${sec.toFixed(0)}秒`;
  return `${Math.floor(sec / 60)}分${Math.round(sec % 60)}秒`;
}

function formatParams(params: Record<string, unknown>): string {
  const entries = Object.entries(params);
  if (entries.length === 0) return "";
  return entries.map(([k, v]) => `${k}=${v}`).join(", ");
}

function ResultRow({ r }: { r: CaseResult }) {
  const q = r.metrics.quality_score;
  const paramStr = formatParams(r.params);
  const badge = r.privacy_risk ? PRIVACY_BADGE[r.privacy_risk] : null;

  return (
    <tr className="border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors">
      <td className="py-1.5 pr-2">
        <Link
          to={`/algorithm/${r.algorithm_id}`}
          className="text-blue-700 hover:text-blue-900 font-medium hover:underline"
        >
          {r.algorithm_name}
        </Link>
        {paramStr && (
          <span className="text-gray-400 text-xs ml-1">({paramStr})</span>
        )}
      </td>
      <td className="py-1.5 px-1 text-xs text-gray-500">{r.library}</td>
      <td className="py-1.5 px-1 text-right font-mono text-xs">
        {q != null ? (
          <span className={q >= 0.8 ? "text-green-700" : q >= 0.7 ? "text-yellow-700" : "text-red-600"}>
            {(q * 100).toFixed(0)}%
          </span>
        ) : (
          <span className="text-gray-300">-</span>
        )}
      </td>
      <td className="py-1.5 px-1 text-right font-mono text-xs text-gray-600">
        {r.metrics.time_sec != null ? formatTime(r.metrics.time_sec) : "-"}
      </td>
      <td className="py-1.5 pl-1 text-right">
        {badge ? (
          <span className={`text-xs px-1.5 py-0.5 rounded-full ${badge.bg} ${badge.text}`}>
            {badge.label}
          </span>
        ) : (
          <span className="text-gray-300 text-xs">-</span>
        )}
      </td>
    </tr>
  );
}

export function ExperimentCaseCard({ experimentCase }: { experimentCase: ExperimentCase }) {
  const c = experimentCase;
  const icon = DATA_CATEGORY_ICONS[c.data_category];
  const categoryLabel = DATA_CATEGORY_LABELS[c.data_category];

  // Sort results by quality_score descending
  const sortedResults = [...c.results].sort((a, b) => {
    const aq = a.metrics.quality_score ?? -1;
    const bq = b.metrics.quality_score ?? -1;
    return bq - aq;
  });

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden">
      {/* Header */}
      <div className="px-5 pt-4 pb-3">
        <div className="flex items-start gap-2 mb-2">
          <span className="text-lg shrink-0">{icon}</span>
          <div className="min-w-0">
            <h3 className="font-bold text-gray-900 text-sm leading-snug">
              {c.title}
            </h3>
            <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-medium">
              {categoryLabel}
            </span>
          </div>
        </div>

        {/* Scenario */}
        <p className="text-xs text-gray-600 leading-relaxed mt-2">
          {c.scenario.description}
        </p>

        {/* Dataset info */}
        <div className="mt-3 bg-gray-50 rounded-lg px-3 py-2">
          <div className="flex items-baseline gap-2 text-xs">
            <span className="font-semibold text-gray-700">データ:</span>
            <span className="text-gray-600">{c.dataset.name}</span>
            <span className="text-gray-400">|</span>
            <span className="text-gray-500">{c.dataset.rows.toLocaleString()}行 × {c.dataset.columns}列</span>
          </div>
          <div className="flex flex-wrap gap-1 mt-1.5">
            {c.dataset.features.slice(0, 6).map((f) => (
              <span key={f} className="text-xs px-1.5 py-0.5 bg-white border border-gray-200 rounded text-gray-500">
                {f}
              </span>
            ))}
            {c.dataset.features.length > 6 && (
              <span className="text-xs text-gray-400">+{c.dataset.features.length - 6}</span>
            )}
          </div>
        </div>
      </div>

      {/* Results table */}
      <div className="px-5 pb-2">
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
          手法別の結果
        </h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-400">
              <th className="text-left pb-1 font-normal">手法</th>
              <th className="text-left pb-1 font-normal px-1">Lib</th>
              <th className="text-right pb-1 font-normal px-1">品質</th>
              <th className="text-right pb-1 font-normal px-1">時間</th>
              <th className="text-right pb-1 font-normal pl-1">Privacy</th>
            </tr>
          </thead>
          <tbody>
            {sortedResults.map((r, i) => (
              <ResultRow key={`${r.algorithm_id}-${r.library}-${i}`} r={r} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Recommendation */}
      <div className="px-5 py-3 bg-blue-50/50 border-t border-gray-100">
        <p className="text-xs text-blue-800 leading-relaxed">
          <span className="font-semibold">💡 おすすめ:</span> {c.recommendation}
        </p>
      </div>
    </div>
  );
}
