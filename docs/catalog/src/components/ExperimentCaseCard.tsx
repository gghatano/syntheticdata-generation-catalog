import { Link } from "react-router-dom";
import type { ExperimentCase } from "../types/experiment-case";
import { DATA_CATEGORY_LABELS, DATA_CATEGORY_ICONS } from "../types/experiment-case";

export function ExperimentCaseCard({ experimentCase }: { experimentCase: ExperimentCase }) {
  const c = experimentCase;
  const icon = DATA_CATEGORY_ICONS[c.data_category];
  const categoryLabel = DATA_CATEGORY_LABELS[c.data_category];

  const completedResults = c.results.filter((r) => r.metrics.quality_score != null);
  const bestQuality = completedResults.length > 0
    ? Math.max(...completedResults.map((r) => r.metrics.quality_score!))
    : null;

  return (
    <Link
      to={`/case/${c.id}`}
      className="block bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-lg hover:border-blue-300 transition-all duration-300 overflow-hidden group"
    >
      {/* Header */}
      <div className="px-5 pt-4 pb-3">
        <div className="flex items-start gap-2 mb-2">
          <span className="text-lg shrink-0">{icon}</span>
          <div className="min-w-0">
            <h3 className="font-bold text-gray-900 text-sm leading-snug group-hover:text-blue-700 transition-colors">
              {c.title}
            </h3>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-medium">
                {categoryLabel}
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                {c.scenario.use_case}
              </span>
            </div>
          </div>
        </div>

        {/* Scenario (truncated) */}
        <p className="text-xs text-gray-500 leading-relaxed mt-2 line-clamp-2">
          {c.scenario.description}
        </p>

        {/* Dataset summary */}
        <div className="mt-3 flex items-baseline gap-2 text-xs">
          <span className="font-semibold text-gray-700">{c.dataset.name}</span>
          <span className="text-gray-400">
            {c.dataset.rows.toLocaleString()}行 × {c.dataset.columns}列
          </span>
        </div>
      </div>

      {/* Footer */}
      <div className="px-5 py-3 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>{c.results.length} 手法で実験</span>
          {bestQuality != null && (
            <>
              <span className="text-gray-300">|</span>
              <span>最高 Quality <span className="font-semibold text-gray-700">{(bestQuality * 100).toFixed(0)}%</span></span>
            </>
          )}
        </div>
        <span className="text-xs text-blue-600 font-medium group-hover:text-blue-800">
          詳細 →
        </span>
      </div>
    </Link>
  );
}
