import { useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { useExperimentCases } from "../hooks/useExperimentCases";
import { DATA_CATEGORY_LABELS, DATA_CATEGORY_ICONS } from "../types/experiment-case";
import type { CaseResult } from "../types/experiment-case";
import type { TableData } from "../utils/export";
import { ExportButtons } from "../components/ExportButtons";
import { MetricsBarChart } from "../components/MetricsBarChart";

const PRIVACY_BADGE: Record<string, { label: string; bg: string; text: string; border: string }> = {
  low: { label: "低リスク", bg: "bg-green-50", text: "text-green-700", border: "border-green-200" },
  medium: { label: "中リスク", bg: "bg-yellow-50", text: "text-yellow-700", border: "border-yellow-200" },
  high: { label: "高リスク", bg: "bg-red-50", text: "text-red-700", border: "border-red-200" },
};

function formatTime(sec: number): string {
  if (sec < 60) return `${sec.toFixed(1)}秒`;
  const min = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  if (min < 60) return `${min}分${s}秒`;
  return `${Math.floor(min / 60)}時間${min % 60}分`;
}

function formatParams(params: Record<string, unknown>): string {
  const entries = Object.entries(params);
  if (entries.length === 0) return "デフォルト";
  return entries.map(([k, v]) => `${k}=${v}`).join(", ");
}

function qualityColor(q: number): string {
  if (q >= 0.8) return "bg-green-100 text-green-800";
  if (q >= 0.7) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

function dcrColor(d: number): string {
  if (d >= 0.4) return "bg-green-100 text-green-800";
  if (d >= 0.2) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

function ResultRow({ r, index }: { r: CaseResult; index: number }) {
  const badge = r.privacy_risk ? PRIVACY_BADGE[r.privacy_risk] : null;
  const q = r.metrics.quality_score;
  const dcr = r.metrics.dcr_mean;

  return (
    <tr className={`border-b border-gray-100 ${index % 2 === 0 ? "bg-white" : "bg-gray-50/50"} hover:bg-blue-50/50 transition-colors`}>
      <td className="px-4 py-3">
        <Link
          to={`/algorithm/${r.algorithm_id}`}
          className="text-blue-700 hover:text-blue-900 font-semibold hover:underline"
        >
          {r.algorithm_name}
        </Link>
        <span className="text-gray-400 text-xs ml-1.5">({r.library})</span>
      </td>
      <td className="px-4 py-3 text-xs text-gray-500 font-mono">{formatParams(r.params)}</td>
      <td className="px-4 py-3 text-center">
        {q != null ? (
          <span className={`px-2 py-0.5 rounded text-xs font-mono font-semibold ${qualityColor(q)}`}>
            {(q * 100).toFixed(1)}%
          </span>
        ) : <span className="text-gray-300">—</span>}
      </td>
      <td className="px-4 py-3 text-center font-mono text-xs">
        {r.metrics.tstr_f1 != null ? (
          <span className="text-gray-700">{r.metrics.tstr_f1.toFixed(3)}</span>
        ) : <span className="text-gray-300">—</span>}
      </td>
      <td className="px-4 py-3 text-center">
        {dcr != null ? (
          <span className={`px-2 py-0.5 rounded text-xs font-mono ${dcrColor(dcr)}`}>
            {dcr.toFixed(3)}
          </span>
        ) : <span className="text-gray-300">—</span>}
      </td>
      <td className="px-4 py-3 text-right text-xs text-gray-600 whitespace-nowrap">
        {r.metrics.time_sec != null ? formatTime(r.metrics.time_sec) : "—"}
      </td>
      <td className="px-4 py-3 text-center">
        {badge ? (
          <span className={`text-xs px-2 py-0.5 rounded-full border ${badge.bg} ${badge.text} ${badge.border}`}>
            {badge.label}
          </span>
        ) : <span className="text-gray-300 text-xs">—</span>}
      </td>
    </tr>
  );
}

export function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { cases, loading, error } = useExperimentCases();

  const c = cases.find((x) => x.id === id);

  const sortedResults = useMemo(
    () =>
      c
        ? [...c.results].sort((a, b) => {
            const aq = a.metrics.quality_score ?? -1;
            const bq = b.metrics.quality_score ?? -1;
            return bq - aq;
          })
        : [],
    [c]
  );

  const exportData: TableData = useMemo(() => {
    const headers = ["手法", "ライブラリ", "パラメータ", "Quality", "TSTR F1", "DCR", "時間(秒)", "Privacy"];
    const rows = sortedResults.map((r) => [
      r.algorithm_name,
      r.library,
      formatParams(r.params),
      r.metrics.quality_score != null ? (r.metrics.quality_score * 100).toFixed(1) + "%" : "",
      r.metrics.tstr_f1?.toFixed(3) ?? "",
      r.metrics.dcr_mean?.toFixed(3) ?? "",
      r.metrics.time_sec?.toFixed(1) ?? "",
      r.privacy_risk ? PRIVACY_BADGE[r.privacy_risk]?.label ?? "" : "",
    ]);
    return { headers, rows };
  }, [sortedResults]);

  if (loading) return <div className="flex justify-center py-20 text-gray-500">読み込み中...</div>;
  if (error) return <div className="flex justify-center py-20 text-red-500">エラー: {error}</div>;
  if (!c) return <div className="flex justify-center py-20 text-gray-500">事例が見つかりません</div>;

  const icon = DATA_CATEGORY_ICONS[c.data_category];
  const categoryLabel = DATA_CATEGORY_LABELS[c.data_category];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Back link */}
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 mb-6">
        ← 事例一覧に戻る
      </Link>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">{icon}</span>
          <span className="px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 text-sm font-medium">
            {categoryLabel}
          </span>
          <span className="px-3 py-1 rounded-full bg-gray-100 text-gray-600 text-sm">
            {c.scenario.use_case}
          </span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mt-2">{c.title}</h1>
      </div>

      {/* Scenario */}
      <div className="bg-slate-50 rounded-xl p-6 mb-6">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">シナリオ</h2>
        <p className="text-gray-700 leading-relaxed">{c.scenario.description}</p>
      </div>

      {/* Dataset */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">使用データ</h2>
        <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 mb-3">
          {c.dataset.source_url ? (
            <a
              href={c.dataset.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-lg font-bold text-blue-700 hover:text-blue-900 hover:underline inline-flex items-center gap-1"
            >
              {c.dataset.name}
              <svg className="w-4 h-4 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          ) : (
            <span className="text-lg font-bold text-gray-900">{c.dataset.name}</span>
          )}
          <span className="text-sm text-gray-500">
            {c.dataset.rows.toLocaleString()}行 × {c.dataset.columns}列
          </span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {c.dataset.features.map((f) => (
            <span key={f} className="text-xs px-2 py-1 bg-gray-100 border border-gray-200 rounded-md text-gray-600">
              {f}
            </span>
          ))}
        </div>
      </div>

      {/* Metrics Chart */}
      <MetricsBarChart results={sortedResults} />

      {/* Results */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
            手法別の実験結果 ({sortedResults.length}手法)
          </h2>
          <ExportButtons data={exportData} filenameBase={c.id} />
        </div>
        <div className="overflow-x-auto border border-gray-200 rounded-xl">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-600">手法</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-600">パラメータ</th>
                <th className="px-4 py-3 text-center font-semibold text-gray-600">Quality</th>
                <th className="px-4 py-3 text-center font-semibold text-gray-600">TSTR F1</th>
                <th className="px-4 py-3 text-center font-semibold text-gray-600">DCR</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-600">時間</th>
                <th className="px-4 py-3 text-center font-semibold text-gray-600">Privacy</th>
              </tr>
            </thead>
            <tbody>
              {sortedResults.map((r, i) => (
                <ResultRow key={`${r.algorithm_id}-${r.library}-${i}`} r={r} index={i} />
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          * Quality Score は SDMetrics による統計的類似性評価（0〜1）。TSTR F1 は合成データで学習→実データでテスト時の F1 スコア（ベースライン: 0.851）。DCR は最近傍距離の平均（高いほどプライバシー保護が強い）。
        </p>
      </div>

      {/* Recommendation */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-blue-600 uppercase tracking-wider mb-2">💡 おすすめ・考察</h2>
        <p className="text-blue-900 leading-relaxed">{c.recommendation}</p>
      </div>
    </div>
  );
}
