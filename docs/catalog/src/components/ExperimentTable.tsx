import type { Experiment } from "../types/algorithm";

type ExperimentTableProps = {
  experiments: Experiment[];
};

// Baseline: TRTR accuracy=0.8558, f1=0.8513
const BASELINE_ACC = 0.8558;
const BASELINE_F1 = 0.8513;

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

export function ExperimentTable({ experiments }: ExperimentTableProps) {
  if (experiments.length === 0) {
    return <p className="text-gray-500 text-sm">実験データがありません。</p>;
  }

  const hasQuality = experiments.some((e) => e.metrics.quality_score != null);
  const hasTstrAcc = experiments.some((e) => e.metrics.tstr_accuracy != null);
  const hasTstrF1 = experiments.some((e) => e.metrics.tstr_f1 != null);
  const hasDcr = experiments.some((e) => e.metrics.dcr_mean != null);
  const hasTime = experiments.some((e) => e.metrics.time_sec != null);

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-100 text-left border-b-2 border-gray-200">
              <th className="px-3 py-2.5 font-semibold text-gray-700">Library</th>
              <th className="px-3 py-2.5 font-semibold text-gray-700">Params</th>
              {hasQuality && (
                <th className="px-3 py-2.5 font-semibold text-gray-700 text-right">Quality</th>
              )}
              {hasTstrAcc && (
                <th className="px-3 py-2.5 font-semibold text-gray-700 text-right">TSTR Acc</th>
              )}
              {hasTstrF1 && (
                <th className="px-3 py-2.5 font-semibold text-gray-700 text-right">TSTR F1</th>
              )}
              {hasDcr && (
                <th className="px-3 py-2.5 font-semibold text-gray-700 text-right">DCR Mean</th>
              )}
              {hasTime && (
                <th className="px-3 py-2.5 font-semibold text-gray-700 text-right">実行時間</th>
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
