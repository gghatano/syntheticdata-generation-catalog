import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Experiment } from "../types/algorithm";

const QUALITY_COLOR = "#2563eb";
const TSTR_COLOR = "#10b981";
const DCR_COLOR = "#f97316";

type LibrarySummary = {
  library: string;
  experiment_count: number;
  quality_score?: number;
  tstr_f1?: number;
  dcr_mean?: number;
  time_sec?: number;
  params_text: string;
};

function pickBestExperiment(experiments: Experiment[]): Experiment {
  // Quality 最高の experiment を採用。Quality が無ければ TSTR F1、それも無ければ最初の experiment
  const sorted = [...experiments].sort((a, b) => {
    const aq = a.metrics.quality_score ?? a.metrics.tstr_f1 ?? -1;
    const bq = b.metrics.quality_score ?? b.metrics.tstr_f1 ?? -1;
    return bq - aq;
  });
  return sorted[0];
}

function summarizeByLibrary(experiments: Experiment[]): LibrarySummary[] {
  const grouped = new Map<string, Experiment[]>();
  for (const exp of experiments) {
    const lib = exp.library;
    if (!grouped.has(lib)) grouped.set(lib, []);
    grouped.get(lib)!.push(exp);
  }
  const summaries: LibrarySummary[] = [];
  for (const [library, exps] of grouped) {
    const best = pickBestExperiment(exps);
    const paramEntries = Object.entries(best.params);
    const params_text =
      paramEntries.length === 0
        ? "default"
        : paramEntries.map(([k, v]) => `${k}=${v}`).join(", ");
    summaries.push({
      library,
      experiment_count: exps.length,
      quality_score: best.metrics.quality_score,
      tstr_f1: best.metrics.tstr_f1,
      dcr_mean: best.metrics.dcr_mean,
      time_sec: best.metrics.time_sec,
      params_text,
    });
  }
  // Quality 降順で固定（読み手が「上位」を見やすいよう）
  summaries.sort((a, b) => (b.quality_score ?? -1) - (a.quality_score ?? -1));
  return summaries;
}

function buildInsightText(summaries: LibrarySummary[], algorithmName: string): string | null {
  if (summaries.length < 2) return null;
  const withQuality = summaries.filter((s) => s.quality_score != null);
  if (withQuality.length < 2) return null;
  const top = withQuality[0];
  const bottom = withQuality[withQuality.length - 1];
  const diff = (top.quality_score! - bottom.quality_score!).toFixed(2);
  return (
    `同じ ${algorithmName} でも ${top.library} 版は Quality ${top.quality_score!.toFixed(2)}、` +
    `${bottom.library} 版は Quality ${bottom.quality_score!.toFixed(2)} と ${diff} の差。`
  );
}

export function LibraryComparisonChart({
  experiments,
  algorithmName,
}: {
  experiments: Experiment[];
  algorithmName: string;
}) {
  const summaries = summarizeByLibrary(experiments);
  if (summaries.length < 2) return null;

  const chartData = summaries.map((s) => ({
    name: s.library,
    Quality: s.quality_score != null ? Math.round(s.quality_score * 1000) / 1000 : null,
    "TSTR F1": s.tstr_f1 != null ? Math.round(s.tstr_f1 * 1000) / 1000 : null,
    "DCR Mean": s.dcr_mean != null ? Math.round(s.dcr_mean * 1000) / 1000 : null,
  }));

  const insight = buildInsightText(summaries, algorithmName);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="mb-3">
        <h2 className="font-semibold text-gray-800 text-lg">ライブラリ間比較</h2>
        <p className="text-xs text-gray-500 mt-1 leading-relaxed">
          同じ {algorithmName} アルゴリズムを各ライブラリが実装した場合の Quality / TSTR F1 / DCR Mean を比較。各ライブラリの代表値は Quality 最高の実験を採用。
        </p>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#374151" }} />
            <YAxis domain={[0, 1]} tick={{ fontSize: 11, fill: "#6b7280" }} />
            <Tooltip
              contentStyle={{ fontSize: 12 }}
              formatter={(value) =>
                typeof value === "number" ? value.toFixed(3) : value
              }
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="Quality" fill={QUALITY_COLOR} fillOpacity={0.85} />
            <Bar dataKey="TSTR F1" fill={TSTR_COLOR} fillOpacity={0.85} />
            <Bar dataKey="DCR Mean" fill={DCR_COLOR} fillOpacity={0.85} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {insight ? (
        <p className="text-sm text-blue-900 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 mt-3 leading-relaxed">
          💡 {insight}
        </p>
      ) : null}

      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-200">
              <th className="px-2 py-1.5 font-semibold">ライブラリ</th>
              <th className="px-2 py-1.5 font-semibold">代表 params</th>
              <th className="px-2 py-1.5 font-semibold text-right">実験数</th>
              <th className="px-2 py-1.5 font-semibold text-right">Quality</th>
              <th className="px-2 py-1.5 font-semibold text-right">TSTR F1</th>
              <th className="px-2 py-1.5 font-semibold text-right">DCR Mean</th>
              <th className="px-2 py-1.5 font-semibold text-right">時間 (秒)</th>
            </tr>
          </thead>
          <tbody>
            {summaries.map((s) => (
              <tr key={s.library} className="border-b border-gray-100">
                <td className="px-2 py-1.5 font-medium">{s.library}</td>
                <td className="px-2 py-1.5 font-mono text-gray-600">{s.params_text}</td>
                <td className="px-2 py-1.5 text-right text-gray-600">{s.experiment_count}</td>
                <td className="px-2 py-1.5 text-right font-mono">
                  {s.quality_score != null ? s.quality_score.toFixed(3) : "—"}
                </td>
                <td className="px-2 py-1.5 text-right font-mono">
                  {s.tstr_f1 != null ? s.tstr_f1.toFixed(3) : "—"}
                </td>
                <td className="px-2 py-1.5 text-right font-mono">
                  {s.dcr_mean != null ? s.dcr_mean.toFixed(3) : "—"}
                </td>
                <td className="px-2 py-1.5 text-right text-gray-500">
                  {s.time_sec != null ? s.time_sec.toFixed(1) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
