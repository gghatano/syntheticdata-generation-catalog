import { useParams, Link } from "react-router-dom";
import { useAlgorithms } from "../hooks/useAlgorithms";
import { CATEGORY_LABELS, DATA_TYPE_LABELS } from "../constants/categories";
import { MetricsBadge } from "../components/MetricsBadge";
import { ExperimentTable } from "../components/ExperimentTable";

export function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const { algorithms, loading, error } = useAlgorithms();

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <span className="text-gray-500">読み込み中...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center py-20">
        <span className="text-red-500">エラー: {error}</span>
      </div>
    );
  }

  const algorithm = algorithms.find((a) => a.id === id);

  if (!algorithm) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-500 mb-4">アルゴリズムが見つかりません。</p>
        <Link to="/" className="text-blue-600 hover:underline">
          一覧に戻る
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/" className="text-blue-600 hover:underline text-sm mb-4 inline-block">
        &larr; 一覧に戻る
      </Link>

      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-800">{algorithm.name}</h2>
          <div className="flex gap-2 items-center">
            <span className="bg-blue-100 text-blue-800 text-sm font-medium px-3 py-1 rounded">
              {CATEGORY_LABELS[algorithm.category]}
            </span>
            {algorithm.privacy_risk_level && (
              <MetricsBadge level={algorithm.privacy_risk_level} />
            )}
          </div>
        </div>

        <p className="text-gray-600 mb-4">{algorithm.description}</p>

        {/* Metadata */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <h4 className="font-semibold text-gray-700 mb-1">対応データタイプ</h4>
            <div className="flex flex-wrap gap-1">
              {algorithm.supported_data.map((dt) => (
                <span key={dt} className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs">
                  {DATA_TYPE_LABELS[dt]}
                </span>
              ))}
            </div>
          </div>
          <div>
            <h4 className="font-semibold text-gray-700 mb-1">ライブラリ</h4>
            <div className="flex flex-wrap gap-1">
              {algorithm.libraries.map((lib) => (
                <span key={lib} className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs">
                  {lib}
                </span>
              ))}
            </div>
          </div>
        </div>

        {algorithm.reference && (
          <div className="mt-4 text-sm">
            <span className="font-semibold text-gray-700">参考: </span>
            <a
              href={algorithm.reference}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline break-all"
            >
              {algorithm.reference}
            </a>
          </div>
        )}
      </div>

      {/* Tags / Use Cases */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold text-gray-700 mb-2">タグ</h3>
            <div className="flex flex-wrap gap-1">
              {algorithm.tags.map((tag) => (
                <span key={tag} className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs">
                  {tag}
                </span>
              ))}
            </div>
          </div>
          <div>
            <h3 className="font-semibold text-gray-700 mb-2">ユースケース</h3>
            <div className="flex flex-wrap gap-1">
              {algorithm.use_cases.map((uc) => (
                <span key={uc} className="bg-green-50 text-green-700 px-2 py-0.5 rounded text-xs">
                  {uc}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Strengths / Weaknesses */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold text-green-700 mb-2">強み</h3>
            <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
              {algorithm.strengths.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-red-700 mb-2">弱み</h3>
            <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
              {algorithm.weaknesses.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Summary Metrics */}
      {algorithm.summary_metrics && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="font-semibold text-gray-700 mb-3">サマリメトリクス</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {algorithm.summary_metrics.best_quality_score.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500">Quality Score</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {algorithm.summary_metrics.best_tstr_f1.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500">TSTR F1</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {algorithm.summary_metrics.best_dcr_mean.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500">DCR Mean</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {algorithm.summary_metrics.fastest_time_sec.toFixed(1)}s
              </div>
              <div className="text-xs text-gray-500">Fastest Time</div>
            </div>
          </div>
        </div>
      )}

      {/* Experiments */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="font-semibold text-gray-700 mb-3">実験結果</h3>
        <ExperimentTable experiments={algorithm.experiments} />
      </div>
    </div>
  );
}
