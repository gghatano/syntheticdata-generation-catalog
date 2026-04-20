import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useAlgorithms } from "../hooks/useAlgorithms";
import { CATEGORY_LABELS, DATA_TYPE_LABELS } from "../constants/categories";
import { MetricsBadge } from "../components/MetricsBadge";
import { ExperimentTable } from "../components/ExperimentTable";
import { QuickStartSection } from "../components/QuickStartSection";
import type { PrivacyRiskLevel } from "../types/algorithm";

const PRIVACY_MECHANISM_LABELS: Record<string, string> = {
  none: "なし（プライバシー保護機構なし）",
  identifiability_penalty: "識別可能性ペナルティ（生成データが元データに近づきすぎないよう制約）",
  differential_privacy: "差分プライバシー（数学的なプライバシー保証）",
};

const PRIVACY_BANNER_KEY = "syntheticdata-catalog-privacy-banner-dismissed";

const PRIVACY_RISK_RATIONALE: Record<PrivacyRiskLevel, string> = {
  low: "DCR 5th percentile > 0.2: 最も近い合成レコードでも元データから十分な距離があります",
  medium:
    "DCR 5th percentile 0.05〜0.2: 一部の合成レコードが元データに近い可能性があります",
  high: "DCR 5th percentile < 0.05: 元データに非常に近い合成レコードが存在する可能性があり、再識別リスクがあります",
};

function PrivacyWarningBanner() {
  const [dismissed, setDismissed] = useState(() => {
    try {
      return localStorage.getItem(PRIVACY_BANNER_KEY) === "1";
    } catch {
      return false;
    }
  });

  if (dismissed) return null;

  const handleDismiss = () => {
    setDismissed(true);
    try {
      localStorage.setItem(PRIVACY_BANNER_KEY, "1");
    } catch {
      // ignore
    }
  };

  return (
    <div className="bg-amber-50 border border-amber-300 rounded-lg px-4 py-3 mb-6 flex items-start gap-3">
      <span className="text-lg shrink-0 mt-0.5" aria-hidden="true">&#9888;&#65039;</span>
      <p className="text-sm text-amber-900 flex-1">
        合成データは匿名データではありません。本番データに適用する前に、データの性質・用途に応じたプライバシー評価を実施してください。
      </p>
      <button
        onClick={handleDismiss}
        className="text-amber-600 hover:text-amber-800 text-lg font-bold leading-none shrink-0 cursor-pointer"
        aria-label="閉じる"
      >
        &times;
      </button>
    </div>
  );
}

const CATEGORY_COLORS: Record<string, string> = {
  gan: "bg-purple-100 text-purple-800",
  vae: "bg-indigo-100 text-indigo-800",
  copula: "bg-blue-100 text-blue-800",
  bayesian: "bg-teal-100 text-teal-800",
  flow: "bg-cyan-100 text-cyan-800",
  sequential: "bg-orange-100 text-orange-800",
};

export function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const { algorithms, loading, error } = useAlgorithms();

  const algorithm = algorithms.find((a) => a.id === id);

  useEffect(() => {
    if (algorithm) {
      document.title = `${algorithm.name} | 合成データ生成手法カタログ`;
    }
    return () => {
      document.title = "合成データ生成手法カタログ";
    };
  }, [algorithm]);

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

  const categoryColor = CATEGORY_COLORS[algorithm.category] ?? "bg-gray-100 text-gray-800";

  return (
    <div className="max-w-4xl mx-auto">
      {/* ===== 注意バナー ===== */}
      <PrivacyWarningBanner />

      {/* ===== A. ヘッダーセクション ===== */}
      <div className="mb-6">
        <Link
          to="/"
          className="text-blue-600 hover:text-blue-800 text-sm mb-4 inline-flex items-center gap-1 transition-colors"
        >
          <span>&larr;</span>
          <span>一覧に戻る</span>
        </Link>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">{algorithm.name}</h1>

          <div className="flex flex-wrap gap-2 items-center">
            {/* カテゴリバッジ */}
            <span className={`text-sm font-semibold px-3 py-1 rounded-full ${categoryColor}`}>
              {CATEGORY_LABELS[algorithm.category]}
            </span>

            {/* ライブラリバッジ */}
            {algorithm.libraries.map((lib) => (
              <span
                key={lib}
                className="bg-gray-100 text-gray-700 text-sm font-medium px-3 py-1 rounded-full"
              >
                {lib}
              </span>
            ))}

            {/* プライバシーリスクバッジ + 判定根拠 */}
            {algorithm.privacy_risk_level && (
              <MetricsBadge level={algorithm.privacy_risk_level} />
            )}
          </div>

          {/* プライバシーリスク判定根拠 */}
          {algorithm.privacy_risk_level && (
            <div className="mt-3 text-sm text-gray-600 bg-gray-50 rounded-lg px-4 py-2.5 border border-gray-200">
              <span className="font-semibold text-gray-700">判定根拠: </span>
              {PRIVACY_RISK_RATIONALE[algorithm.privacy_risk_level]}
              {(() => {
                const dcr5th = algorithm.experiments
                  .map((e) => e.metrics.dcr_5th_percentile)
                  .filter((v): v is number => v != null);
                if (dcr5th.length === 0) return null;
                const minVal = Math.min(...dcr5th);
                return (
                  <span className="ml-1 font-mono text-gray-500">
                    (実測値: DCR 5th percentile = {minVal.toFixed(4)})
                  </span>
                );
              })()}
            </div>
          )}

          {/* 対応データタイプ */}
          <div className="mt-3 flex flex-wrap gap-1.5">
            {algorithm.supported_data.map((dt) => (
              <span
                key={dt}
                className="bg-blue-50 text-blue-700 text-xs font-medium px-2.5 py-1 rounded-full border border-blue-200"
              >
                {DATA_TYPE_LABELS[dt]}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ===== B. 概要セクション ===== */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        {/* Description */}
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 mb-6">
          <p className="text-gray-700 leading-relaxed">{algorithm.description}</p>
        </div>

        {/* Strengths / Weaknesses */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-semibold text-green-800 mb-3 flex items-center gap-1.5">
              <span className="text-green-600">&#9650;</span> 強み
            </h3>
            <ul className="space-y-2">
              {algorithm.strengths.map((s, i) => (
                <li key={i} className="text-sm text-green-900 flex items-start gap-2">
                  <span className="text-green-500 mt-0.5 shrink-0">&#10003;</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="font-semibold text-red-800 mb-3 flex items-center gap-1.5">
              <span className="text-red-600">&#9660;</span> 弱み
            </h3>
            <ul className="space-y-2">
              {algorithm.weaknesses.map((w, i) => (
                <li key={i} className="text-sm text-red-900 flex items-start gap-2">
                  <span className="text-red-400 mt-0.5 shrink-0">&#10007;</span>
                  <span>{w}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* ===== C. タグセクション ===== */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {/* Tags */}
          <div>
            <h3 className="font-semibold text-gray-700 mb-2 text-sm uppercase tracking-wide">
              タグ
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {algorithm.tags.map((tag) => (
                <span
                  key={tag}
                  className="bg-blue-50 text-blue-700 px-2.5 py-1 rounded-full text-xs font-medium border border-blue-200 hover:bg-blue-100 cursor-pointer transition-colors"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Use Cases */}
          <div>
            <h3 className="font-semibold text-gray-700 mb-2 text-sm uppercase tracking-wide">
              ユースケース
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {algorithm.use_cases.map((uc) => (
                <span
                  key={uc}
                  className="bg-green-50 text-green-700 px-2.5 py-1 rounded-full text-xs font-medium border border-green-200 hover:bg-green-100 cursor-pointer transition-colors"
                >
                  {uc}
                </span>
              ))}
            </div>
          </div>

          {/* Input Requirements */}
          <div>
            <h3 className="font-semibold text-gray-700 mb-2 text-sm uppercase tracking-wide">
              入力要件
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {algorithm.input_requirements.map((req) => (
                <span
                  key={req}
                  className="bg-amber-50 text-amber-700 px-2.5 py-1 rounded-full text-xs font-medium border border-amber-200 hover:bg-amber-100 cursor-pointer transition-colors"
                >
                  {req}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ===== D. 実験結果セクション ===== */}
      {/* Summary Metrics */}
      {algorithm.summary_metrics && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="font-semibold text-gray-800 text-lg mb-4">サマリメトリクス</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {algorithm.summary_metrics.best_quality_score != null && (
              <div className="bg-slate-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {algorithm.summary_metrics.best_quality_score.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500 mt-1">Best Quality</div>
              </div>
            )}
            {algorithm.summary_metrics.best_tstr_f1 != null && (
              <div className="bg-slate-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {algorithm.summary_metrics.best_tstr_f1.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500 mt-1">Best TSTR F1</div>
              </div>
            )}
            {algorithm.summary_metrics.best_dcr_mean != null && (
              <div className="bg-slate-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {algorithm.summary_metrics.best_dcr_mean.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500 mt-1">Best DCR Mean</div>
              </div>
            )}
            <div className="bg-slate-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">
                {algorithm.summary_metrics.fastest_time_sec.toFixed(1)}
                <span className="text-sm font-normal text-gray-500">s</span>
              </div>
              <div className="text-xs text-gray-500 mt-1">Fastest Time</div>
            </div>
          </div>
        </div>
      )}

      {/* Experiments Table */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="font-semibold text-gray-800 text-lg mb-4">実験結果</h2>
        <ExperimentTable experiments={algorithm.experiments} filenameBase={algorithm.id} />
      </div>

      {/* ===== E. クイックスタートセクション ===== */}
      <QuickStartSection libraries={algorithm.libraries} algorithmId={algorithm.id} />

      {/* ===== F. 参考文献セクション ===== */}
      {(algorithm.reference || algorithm.privacy_mechanism) && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="font-semibold text-gray-800 text-lg mb-4">参考情報</h2>

          {algorithm.reference && (
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-600 mb-1">参考文献</h3>
              <a
                href={algorithm.reference}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 hover:underline text-sm break-all inline-flex items-center gap-1"
              >
                <span>{algorithm.reference}</span>
                <svg
                  className="w-3.5 h-3.5 shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
              </a>
            </div>
          )}

          {algorithm.privacy_mechanism && (
            <div>
              <h3 className="text-sm font-semibold text-gray-600 mb-1">プライバシー機構</h3>
              <p className="text-sm text-gray-700">
                {PRIVACY_MECHANISM_LABELS[algorithm.privacy_mechanism] ??
                  algorithm.privacy_mechanism}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
