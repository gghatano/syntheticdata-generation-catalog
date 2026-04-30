import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTimeSeriesData } from "../hooks/useTimeSeriesData";
import type { TimeSeriesSeries } from "../types/timeseries";

const REAL_COLOR = "#2563eb";
const SYNTH_COLOR = "#f97316";

function SeriesChart({ series }: { series: TimeSeriesSeries }) {
  return (
    <div className="mb-4 last:mb-0">
      <div className="flex items-baseline justify-between mb-1">
        <h4 className="text-sm font-semibold text-gray-700">
          {series.label}
        </h4>
        <span className="text-[11px] text-gray-500 font-mono">
          real μ={series.real_mean} σ={series.real_std}
          <span className="mx-2 text-gray-300">|</span>
          synth μ={series.synth_mean} σ={series.synth_std}
        </span>
      </div>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={series.points}
            margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="x"
              type="number"
              domain={[0, "dataMax"]}
              tick={{ fontSize: 11, fill: "#6b7280" }}
              label={{
                value: "経過日数 (day index)",
                position: "insideBottom",
                offset: -2,
                style: { fontSize: 11, fill: "#6b7280" },
              }}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#6b7280" }}
              label={
                series.unit
                  ? { value: series.unit, angle: -90, position: "insideLeft", style: { fontSize: 11, fill: "#6b7280" } }
                  : undefined
              }
            />
            <Tooltip
              contentStyle={{ fontSize: 12 }}
              labelFormatter={(label) => `day ${label}`}
              formatter={(value, name) => {
                const numeric = typeof value === "number" ? value.toFixed(2) : "—";
                return [numeric, name as string];
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line
              type="monotone"
              dataKey="real"
              name="元データ (real)"
              stroke={REAL_COLOR}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="synth"
              name="合成データ (synth)"
              stroke={SYNTH_COLOR}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function TimeSeriesComparisonChart({ caseId }: { caseId: string }) {
  const { data, loading, error } = useTimeSeriesData(caseId);

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          時系列比較
        </h2>
        <p className="text-sm text-gray-400">時系列データを読み込み中...</p>
      </div>
    );
  }

  if (error || !data) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
          時系列比較
        </h2>
        <p className="text-xs text-gray-500 mt-1 leading-relaxed">
          元データ（青）と合成データ（橙）の振る舞いを比較。real は <span className="font-mono">{data.selected_real_location}</span> の {data.date_range_real.start} – {data.date_range_real.end}（{data.sequence_length} 日間）、synth は PAR 64ep が生成した 1 シーケンス。
        </p>
      </div>
      {data.series.map((s) => (
        <SeriesChart key={s.name} series={s} />
      ))}
      <p className="text-[11px] text-gray-400 leading-relaxed mt-3">
        {data.note} 季節変動・自己相関の再現度を視覚的に確認してください。
      </p>
    </div>
  );
}
