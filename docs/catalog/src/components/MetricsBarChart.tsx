import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { CaseResult } from "../types/experiment-case";

type Props = {
  results: CaseResult[];
};

type ChartRow = {
  name: string;
  quality: number | null;
  tstr: number | null;
  dcr: number | null;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold text-gray-800 mb-1">{label}</p>
      {payload.map((entry: { name: string; value: number | null; color: string }) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name}: {entry.value != null ? entry.value.toFixed(3) : "N/A"}
        </p>
      ))}
    </div>
  );
}

export function MetricsBarChart({ results }: Props) {
  const data: ChartRow[] = results.map((r) => ({
    name: `${r.algorithm_name} (${r.library})`,
    quality: r.metrics.quality_score ?? null,
    tstr: r.metrics.tstr_f1 ?? null,
    dcr: r.metrics.dcr_mean ?? null,
  }));

  const hasQuality = data.some((d) => d.quality != null);
  const hasTstr = data.some((d) => d.tstr != null);
  const hasDcr = data.some((d) => d.dcr != null);

  if (!hasQuality && !hasTstr && !hasDcr) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
        精度比較
      </h2>
      <ResponsiveContainer width="100%" height={Math.max(250, results.length * 50 + 80)}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            type="number"
            domain={[0, 1.2]}
            tickFormatter={(v: number) => v.toFixed(1)}
            fontSize={12}
            stroke="#9ca3af"
          />
          <YAxis
            type="category"
            dataKey="name"
            width={180}
            fontSize={12}
            stroke="#9ca3af"
            tick={{ fill: "#374151" }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }}
          />
          {hasQuality && (
            <Bar
              dataKey="quality"
              name="Quality Score"
              fill="#3b82f6"
              radius={[0, 4, 4, 0]}
              barSize={16}
            />
          )}
          {hasTstr && (
            <Bar
              dataKey="tstr"
              name="TSTR F1"
              fill="#10b981"
              radius={[0, 4, 4, 0]}
              barSize={16}
            />
          )}
          {hasDcr && (
            <Bar
              dataKey="dcr"
              name="DCR Mean"
              fill="#f59e0b"
              radius={[0, 4, 4, 0]}
              barSize={16}
            />
          )}
        </BarChart>
      </ResponsiveContainer>
      <p className="text-xs text-gray-400 mt-2">
        Quality Score・TSTR F1 は高いほど品質が良い。DCR Mean は高いほどプライバシー保護が強い。
      </p>
    </div>
  );
}
