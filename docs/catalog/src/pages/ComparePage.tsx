import { useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAlgorithms } from "../hooks/useAlgorithms";
import { useCompareSelection } from "../hooks/useCompareSelection";
import { CATEGORY_LABELS } from "../constants/categories";
import type { Algorithm, Experiment } from "../types/algorithm";

const BASELINE_F1 = 0.8513;

type MetricRow = {
  key: string;
  label: string;
  formatter: (v: number | undefined | null) => string;
  /** 高いほど良い? */
  higherIsBetter: boolean;
  /** Quality / TSTR / DCR の colorFn 適用範囲（任意）*/
  cellClass?: (v: number | null | undefined, all: (number | null | undefined)[]) => string;
};

function fmtPct(v: number | undefined | null): string {
  if (v == null) return "—";
  return (v * 100).toFixed(1) + "%";
}

function fmtNum3(v: number | undefined | null): string {
  if (v == null) return "—";
  return v.toFixed(3);
}

function fmtTime(v: number | undefined | null): string {
  if (v == null) return "—";
  if (v < 60) return `${v.toFixed(1)}秒`;
  const min = Math.floor(v / 60);
  const sec = v % 60;
  if (min < 60) return `${min}分${sec >= 30 ? "半" : ""}`;
  const hr = Math.floor(min / 60);
  return `${hr}時間${min % 60}分`;
}

/** 同じ列内で値が最良/最悪のセルに色付け。null は無視 */
function rankCellClass(
  value: number | null | undefined,
  allValues: (number | null | undefined)[],
  higherIsBetter: boolean
): string {
  if (value == null) return "";
  const nums = allValues.filter((v): v is number => v != null);
  if (nums.length < 2) return "";
  const best = higherIsBetter ? Math.max(...nums) : Math.min(...nums);
  const worst = higherIsBetter ? Math.min(...nums) : Math.max(...nums);
  if (value === best && best !== worst) return "bg-green-50 text-green-800 font-semibold";
  if (value === worst && best !== worst) return "bg-red-50 text-red-800";
  return "";
}

function pickBest(experiments: Experiment[]): Experiment | undefined {
  if (experiments.length === 0) return undefined;
  return [...experiments].sort((a, b) => {
    const aq = a.metrics.quality_score ?? a.metrics.tstr_f1 ?? -1;
    const bq = b.metrics.quality_score ?? b.metrics.tstr_f1 ?? -1;
    return bq - aq;
  })[0];
}

const METRIC_ROWS: MetricRow[] = [
  {
    key: "quality",
    label: "Quality",
    formatter: fmtPct,
    higherIsBetter: true,
  },
  {
    key: "tstr_f1",
    label: "TSTR F1",
    formatter: (v) => (v == null ? "—" : `${v.toFixed(3)} (vs ベースライン ${BASELINE_F1})`),
    higherIsBetter: true,
  },
  {
    key: "dcr_mean",
    label: "DCR Mean",
    formatter: fmtNum3,
    higherIsBetter: true,
  },
  {
    key: "time",
    label: "実行時間",
    formatter: fmtTime,
    higherIsBetter: false,
  },
];

function getMetricValue(alg: Algorithm, key: string): number | undefined {
  const best = pickBest(alg.experiments);
  if (!best) return undefined;
  switch (key) {
    case "quality":
      return best.metrics.quality_score ?? alg.summary_metrics?.best_quality_score;
    case "tstr_f1":
      return best.metrics.tstr_f1 ?? alg.summary_metrics?.best_tstr_f1;
    case "dcr_mean":
      return best.metrics.dcr_mean ?? alg.summary_metrics?.best_dcr_mean;
    case "time":
      return best.metrics.time_sec ?? alg.summary_metrics?.fastest_time_sec;
    default:
      return undefined;
  }
}

function getRepresentativeDataset(alg: Algorithm): string | undefined {
  const best = pickBest(alg.experiments);
  return best?.dataset;
}

export function ComparePage() {
  const [searchParams] = useSearchParams();
  const { algorithms, loading, error } = useAlgorithms();
  const { selected, remove, clear } = useCompareSelection();

  const ids = useMemo(() => {
    const param = searchParams.get("ids");
    if (param) return param.split(",").map((s) => s.trim()).filter(Boolean);
    // URL に ids が無ければ localStorage の選択を使う
    return selected;
  }, [searchParams, selected]);

  const compared = useMemo(
    () => ids.map((id) => algorithms.find((a) => a.id === id)).filter((a): a is Algorithm => !!a),
    [ids, algorithms]
  );

  if (loading) return <div className="flex justify-center py-20 text-gray-500">読み込み中...</div>;
  if (error) return <div className="flex justify-center py-20 text-red-500">エラー: {error}</div>;

  if (compared.length === 0) {
    return (
      <div className="max-w-4xl mx-auto py-10 text-center">
        <h1 className="text-2xl font-bold text-gray-800 mb-3">比較対象がありません</h1>
        <p className="text-gray-600 mb-6">
          一覧ページで「比較に追加」ボタンを押してアルゴリズムを 2〜3 件選択してから戻ってきてください。
        </p>
        <Link
          to="/"
          className="inline-block bg-blue-600 text-white px-5 py-2.5 rounded-full text-sm font-semibold hover:bg-blue-700"
        >
          一覧ページへ
        </Link>
      </div>
    );
  }

  // 同一データセットでの比較かを判定
  const datasets = new Set(compared.map(getRepresentativeDataset).filter(Boolean) as string[]);
  const sameDataset = datasets.size === 1;

  return (
    <div className="max-w-5xl mx-auto pb-32">
      <Link
        to="/"
        className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 mb-4"
      >
        ← 一覧に戻る
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">手法の横並び比較</h1>
        <p className="text-sm text-gray-600">
          選択した {compared.length} 件のアルゴリズムを Quality / TSTR / DCR / 時間で比較します。各アルゴリズムの代表値は Quality 最高の experiment を採用しています。
        </p>
      </div>

      {!sameDataset && (
        <div
          role="alert"
          className="bg-amber-50 border border-amber-200 text-amber-900 rounded-lg px-4 py-3 mb-4 text-sm"
        >
          ⚠️ 異なるデータセット（
          {Array.from(datasets).join(" / ")}
          ）の結果を並べています。スコアの直接比較には注意してください（同一データセット同士の比較が原則）。
        </div>
      )}

      <div className="overflow-x-auto bg-white rounded-xl border border-gray-200 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-4 py-3 text-left font-semibold text-gray-600 sticky left-0 bg-gray-50 z-10 min-w-[140px]">
                指標
              </th>
              {compared.map((alg) => (
                <th
                  key={alg.id}
                  className="px-4 py-3 text-left font-semibold text-gray-700 align-top min-w-[180px]"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <Link
                        to={`/algorithm/${alg.id}`}
                        className="text-blue-700 hover:underline"
                      >
                        {alg.name}
                      </Link>
                      <div className="text-[11px] text-gray-500 font-normal mt-0.5">
                        {CATEGORY_LABELS[alg.category]} ・{" "}
                        {getRepresentativeDataset(alg) ?? "—"}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => remove(alg.id)}
                      title="比較から外す"
                      aria-label={`${alg.name} を比較から外す`}
                      className="text-gray-400 hover:text-red-600 shrink-0"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {METRIC_ROWS.map((row) => {
              const values = compared.map((alg) => getMetricValue(alg, row.key));
              return (
                <tr key={row.key} className="border-b border-gray-100">
                  <th className="px-4 py-3 text-left font-medium text-gray-700 sticky left-0 bg-white z-10 align-top">
                    {row.label}
                  </th>
                  {compared.map((alg, i) => {
                    const v = values[i];
                    const cls = rankCellClass(v, values, row.higherIsBetter);
                    return (
                      <td
                        key={alg.id}
                        className={`px-4 py-3 align-top ${cls}`.trim()}
                      >
                        {row.formatter(v)}
                      </td>
                    );
                  })}
                </tr>
              );
            })}

            {/* ライブラリと対応データ型の補足 */}
            <tr className="border-b border-gray-100 bg-gray-50/40">
              <th className="px-4 py-3 text-left font-medium text-gray-700 sticky left-0 bg-gray-50/40 z-10 align-top">
                ライブラリ
              </th>
              {compared.map((alg) => (
                <td key={alg.id} className="px-4 py-3 align-top">
                  <div className="flex flex-wrap gap-1">
                    {alg.libraries.map((lib) => (
                      <span
                        key={lib}
                        className="text-[11px] bg-white border border-gray-200 rounded-full px-2 py-0.5 text-gray-600"
                      >
                        {lib}
                      </span>
                    ))}
                  </div>
                </td>
              ))}
            </tr>

            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-700 sticky left-0 bg-white z-10 align-top">
                強み（要約）
              </th>
              {compared.map((alg) => (
                <td key={alg.id} className="px-4 py-3 text-xs text-gray-700 align-top">
                  <ul className="list-disc list-inside space-y-0.5">
                    {alg.strengths.slice(0, 3).map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-4">
        <p className="text-xs text-gray-500">
          色付き: 緑=各指標で最良 / 赤=最悪。null セルは「—」表示。各セルは <Link to="/algorithm" className="hidden" /> 各手法の詳細ページから個別に確認可能。
        </p>
        <button
          type="button"
          onClick={clear}
          className="text-xs text-gray-500 hover:text-gray-700"
        >
          選択をクリア
        </button>
      </div>

      <p className="text-xs text-gray-400 mt-4">
        この URL は <code className="text-[11px]">?ids=...</code> をブックマーク・共有することで状態を保持できます。
      </p>
    </div>
  );
}
