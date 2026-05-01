import {
  Bar,
  BarChart,
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
import type {
  AggregateSeries,
  TimeSeriesPair,
  TimeSeriesSeries,
} from "../types/timeseries";

const REAL_COLOR = "#2563eb";
const SYNTH_COLOR = "#f97316";

function fmtNum(value: number, digits = 2): string {
  if (Math.abs(value) >= 1000) return value.toFixed(0);
  return value.toFixed(digits);
}

function SeriesChart({ series }: { series: TimeSeriesSeries }) {
  return (
    <div className="mb-4 last:mb-0">
      <div className="flex items-baseline justify-between mb-1">
        <h4 className="text-sm font-semibold text-gray-700">
          {series.label}
        </h4>
        <span className="text-[11px] text-gray-500 font-mono">
          real μ={fmtNum(series.real_mean)} σ={fmtNum(series.real_std)}
          <span className="mx-2 text-gray-300">|</span>
          synth μ={fmtNum(series.synth_mean)} σ={fmtNum(series.synth_std)}
        </span>
      </div>
      <div className="h-48 w-full">
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
                const numeric = typeof value === "number" ? fmtNum(value) : "—";
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

function PairBlock({ pair }: { pair: TimeSeriesPair }) {
  return (
    <div className="border border-gray-200 rounded-xl p-4 mb-4 last:mb-0 bg-slate-50/40">
      <div className="mb-2">
        <h3 className="text-sm font-bold text-gray-800">{pair.label}</h3>
        <p className="text-[11px] text-gray-500 mt-0.5 leading-relaxed">
          real: <span className="font-mono">{pair.real_id}</span> ({pair.date_range_real.start} – {pair.date_range_real.end} / {pair.sequence_length} 日間){" "}
          ・ synth: <span className="font-mono">{pair.synth_id}</span>
          {pair.match_reason ? (
            <span className="block text-gray-400 mt-0.5">{pair.match_reason}</span>
          ) : null}
        </p>
      </div>
      {pair.series.map((s) => (
        <SeriesChart key={s.name} series={s} />
      ))}
    </div>
  );
}

function AggregateHistogram({ series }: { series: AggregateSeries }) {
  const data = series.bins.map((b) => ({
    name: fmtNum(b.x, 0),
    real: b.real,
    synth: b.synth,
  }));
  return (
    <div className="mb-4 last:mb-0">
      <div className="flex items-baseline justify-between mb-1 flex-wrap gap-2">
        <h4 className="text-sm font-semibold text-gray-700">
          {series.label}
          {series.unit ? <span className="text-xs font-normal text-gray-500 ml-1">({series.unit})</span> : null}
        </h4>
        <span className="text-[11px] text-gray-500 font-mono">
          real n={series.real_count.toLocaleString()} μ={fmtNum(series.real_mean)}
          <span className="mx-2 text-gray-300">|</span>
          synth n={series.synth_count.toLocaleString()} μ={fmtNum(series.synth_mean)}
        </span>
      </div>
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 10, fill: "#6b7280" }}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} />
            <Tooltip
              contentStyle={{ fontSize: 12 }}
              labelFormatter={(label) => `${series.label}: ${label}`}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="real" name="元データ (real)" fill={REAL_COLOR} fillOpacity={0.85} />
            <Bar dataKey="synth" name="合成データ (synth)" fill={SYNTH_COLOR} fillOpacity={0.85} />
          </BarChart>
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
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
          時系列比較
        </h2>
        <p className="text-xs text-gray-500 mt-1 leading-relaxed">{data.note}</p>
      </div>

      {/* Pair-wise time series */}
      <div className="mb-4">
        {data.pairs.map((p) => (
          <PairBlock key={`${p.real_id}__${p.synth_id}`} pair={p} />
        ))}
      </div>

      {/* Aggregate distribution */}
      {data.aggregate && data.aggregate.series.length > 0 ? (
        <div className="border-t border-gray-200 pt-4 mt-2">
          <h3 className="text-sm font-semibold text-gray-700 mb-1">全体分布の比較</h3>
          {data.aggregate.note ? (
            <p className="text-[11px] text-gray-500 leading-relaxed mb-3">
              {data.aggregate.note}
            </p>
          ) : null}
          {data.aggregate.series.map((s) => (
            <AggregateHistogram key={s.name} series={s} />
          ))}
        </div>
      ) : null}
    </div>
  );
}
