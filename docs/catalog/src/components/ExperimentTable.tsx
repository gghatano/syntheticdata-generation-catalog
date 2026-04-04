import { useMemo } from "react";
import type { Experiment } from "../types/algorithm";
import type { TableData } from "../utils/export";
import { ExportButtons } from "./ExportButtons";

type ExperimentTableProps = {
  experiments: Experiment[];
  filenameBase?: string;
};

// Baseline: TRTR accuracy=0.8558, f1=0.8513
const BASELINE_ACC = 0.8558;
const BASELINE_F1 = 0.8513;

const METRIC_TOOLTIPS: Record<string, string> = {
  quality:
    "元データの統計的特性（分布・相関）をどの程度再現できたかのスコア（0〜1、高いほど良い）",
  tstr_acc:
    "合成データで学習→実データでテスト時の正解率。ベースライン(0.856)に近いほど良い",
  tstr_f1:
    "合成データで学習→実データでテスト時のF1スコア。ベースライン(0.851)に近いほど良い",
  dcr_mean:
    "合成データの各レコードと元データの最近傍距離の平均。高いほどプライバシー保護が強い",
  time:
    "CPU環境での学習+生成の合計時間。環境依存のため相対比較のみ推奨",
};

function TooltipHeader({ label, tooltipKey }: { label: string; tooltipKey: string }) {
  const tip = METRIC_TOOLTIPS[tooltipKey];
  if (!tip) return <>{label}</>;
  return (
    <span className="inline-flex items-center gap-1">
      {label}
      <span className="relative group cursor-help">
        <span className="text-gray-400 text-xs">(&#63;)</span>
        <span
          className="invisible group-hover:visible absolute z-20 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 max-w-xs bg-white text-gray-700 text-sm font-normal rounded-lg shadow-lg border border-gray-200 px-3 py-2 whitespace-normal"
          role="tooltip"
        >
          {tip}
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-white" />
        </span>
      </span>
    </span>
  );
}

function qualityColor(value: number | undefined): string {
  if (value == null) return "";
  if (value >= 0.8) return "bg-green-100 text-green-800";
  if (value >= 0.7) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

function tstrColor(value: number | undefined, baseline: number): string {
  if (value == null) return "";
  const ratio = value / baseline;
  if (ratio >= 0.95) return "bg-green-100 text-green-800";
  if (ratio >= 0.85) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

function dcrColor(value: number | undefined): string {
  if (value == null) return "";
  if (value >= 0.4) return "bg-green-100 text-green-800";
  if (value >= 0.2) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

function formatTime(sec: number | undefined | null): string {
  if (sec == null) return "-";
  if (sec < 60) return `${sec.toFixed(1)}秒`;
  const min = Math.floor(sec / 60);
  const remainSec = sec % 60;
  if (min < 60) {
    return `${sec.toFixed(1)}秒（約${min}分${remainSec >= 30 ? "半" : ""}）`;
  }
  const hr = Math.floor(min / 60);
  const remainMin = min % 60;
  return `${sec.toFixed(1)}秒（約${hr}時間${remainMin}分）`;
}

function formatParams(params: Record<string, unknown>): string {
  const entries = Object.entries(params);
  if (entries.length === 0) return "default";
  return entries.map(([k, v]) => `${k}=${v}`).join(", ");
}

type MetricCellProps = {
  value: number | undefined;
  colorFn: (v: number | undefined) => string;
  digits?: number;
};

function MetricCell({ value, colorFn, digits = 3 }: MetricCellProps) {
  if (value == null) return <td className="px-3 py-2 text-right text-gray-400">-</td>;
  return (
    <td
      className={`px-3 py-2 text-right font-mono text-sm ${colorFn(value)}`}
      title={value.toFixed(4)}
    >
      {value.toFixed(digits)}
    </td>
  );
}

export function ExperimentTable({ experiments, filenameBase = "experiment" }: ExperimentTableProps) {
  if (experiments.length === 0) {
    return <p className="text-gray-500 text-sm">実験データがありません。</p>;
  }

  const hasQuality = experiments.some((e) => e.metrics.quality_score != null);
  const hasTstrAcc = experiments.some((e) => e.metrics.tstr_accuracy != null);
  const hasTstrF1 = experiments.some((e) => e.metrics.tstr_f1 != null);
  const hasDcr = experiments.some((e) => e.metrics.dcr_mean != null);
  const hasTime = experiments.some((e) => e.metrics.time_sec != null);

  const exportData: TableData = useMemo(() => {
    const headers: string[] = ["Library", "Params"];
    if (hasQuality) headers.push("Quality");
    if (hasTstrAcc) headers.push("TSTR Acc");
    if (hasTstrF1) headers.push("TSTR F1");
    if (hasDcr) headers.push("DCR Mean");
    if (hasTime) headers.push("Time (sec)");

    const rows = experiments.map((exp) => {
      const row: string[] = [
        exp.library + (exp.library_version ? ` v${exp.library_version}` : ""),
        formatParams(exp.params),
      ];
      if (hasQuality) row.push(exp.metrics.quality_score?.toFixed(4) ?? "");
      if (hasTstrAcc) row.push(exp.metrics.tstr_accuracy?.toFixed(4) ?? "");
      if (hasTstrF1) row.push(exp.metrics.tstr_f1?.toFixed(4) ?? "");
      if (hasDcr) row.push(exp.metrics.dcr_mean?.toFixed(4) ?? "");
      if (hasTime) row.push(exp.metrics.time_sec?.toFixed(1) ?? "");
      return row;
    });

    return { headers, rows };
  }, [experiments, hasQuality, hasTstrAcc, hasTstrF1, hasDcr, hasTime]);

  return (
    <div>
      {/* エクスポートボタン + 色分け凡例 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-600 bg-gray-50 rounded-lg px-4 py-2.5 border border-gray-200 flex-1 mr-3">
          <span className="font-semibold text-gray-700 mr-1">色分け凡例:</span>
          <span className="inline-flex items-center gap-1"><span className="inline-block w-2.5 h-2.5 rounded-full bg-green-500" /> 良好</span>
          <span className="inline-flex items-center gap-1"><span className="inline-block w-2.5 h-2.5 rounded-full bg-yellow-500" /> 注意</span>
          <span className="inline-flex items-center gap-1"><span className="inline-block w-2.5 h-2.5 rounded-full bg-red-500" /> 要検討</span>
        </div>
        <ExportButtons data={exportData} filenameBase={filenameBase} />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-100 text-left border-b-2 border-gray-200">
              <th className="px-3 py-2.5 font-semibold text-gray-700">Library</th>
              <th className="px-3 py-2.5 font-semibold text-gray-700">Params</th>
              {hasQuality && (
                <th className="px-3 py-2.5 font-semibold text-gray-700 text-right">
                  <TooltipHeader label="Quality" tooltipKey="quality" />
                </th>
              )}
              {hasTstrAcc && (
                <th className="px-3 py-2.5 font-semibold text-gray-700 text-right">
                  <TooltipHeader label="TSTR Acc" tooltipKey="tstr_acc" />
                </th>
              )}
              {hasTstrF1 && (
                <th className="px-3 py-2.5 font-semibold text-gray-700 text-right">
                  <TooltipHeader label="TSTR F1" tooltipKey="tstr_f1" />
                </th>
              )}
              {hasDcr && (
                <th className="px-3 py-2.5 font-semibold text-gray-700 text-right">
                  <TooltipHeader label="DCR Mean" tooltipKey="dcr_mean" />
                </th>
              )}
              {hasTime && (
                <th className="px-3 py-2.5 font-semibold text-gray-700 text-right">
                  <TooltipHeader label="実行時間" tooltipKey="time" />
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {experiments.map((exp, i) => (
              <tr
                key={exp.id}
                className={`border-b border-gray-100 ${
                  i % 2 === 0 ? "bg-white" : "bg-gray-50"
                } hover:bg-blue-50 transition-colors`}
              >
                <td className="px-3 py-2.5">
                  <span className="font-medium">{exp.library}</span>
                  {exp.library_version && (
                    <span className="text-gray-400 ml-1 text-xs">v{exp.library_version}</span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-xs text-gray-600 max-w-48">
                  <span className="bg-gray-100 px-1.5 py-0.5 rounded font-mono">
                    {formatParams(exp.params)}
                  </span>
                </td>
                {hasQuality && (
                  <MetricCell value={exp.metrics.quality_score} colorFn={qualityColor} />
                )}
                {hasTstrAcc && (
                  <MetricCell
                    value={exp.metrics.tstr_accuracy}
                    colorFn={(v) => tstrColor(v, BASELINE_ACC)}
                  />
                )}
                {hasTstrF1 && (
                  <MetricCell
                    value={exp.metrics.tstr_f1}
                    colorFn={(v) => tstrColor(v, BASELINE_F1)}
                  />
                )}
                {hasDcr && <MetricCell value={exp.metrics.dcr_mean} colorFn={dcrColor} />}
                {hasTime && (
                  <td
                    className="px-3 py-2.5 text-right text-sm whitespace-nowrap"
                    title={
                      exp.metrics.time_sec != null
                        ? `${exp.metrics.time_sec.toFixed(4)}秒`
                        : undefined
                    }
                  >
                    {formatTime(exp.metrics.time_sec)}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-400 mt-3">
        * ベースライン（TRTR）: Accuracy = {BASELINE_ACC}, F1 = {BASELINE_F1}
        &nbsp;|&nbsp; セルにカーソルを合わせると正確な値（小数4桁）を表示
      </p>
    </div>
  );
}
