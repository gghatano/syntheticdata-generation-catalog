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
import { useDistributionData } from "../hooks/useDistributionData";
import type {
  CategoricalDistributionItem,
  DistributionItem,
  NumericDistributionItem,
} from "../types/distribution";

const REAL_COLOR = "#2563eb";
const SYNTH_COLOR = "#f97316";

function NumericHistogram({ item }: { item: NumericDistributionItem }) {
  const data = item.bins.map((b) => ({
    name: Number.isFinite(b.x) ? b.x.toFixed(1) : String(b.x),
    real: b.real,
    synth: b.synth,
  }));
  return (
    <div className="mb-4 last:mb-0">
      <div className="flex items-baseline justify-between mb-1">
        <h4 className="text-sm font-semibold text-gray-700">
          {item.label}
          {item.unit ? <span className="text-xs font-normal text-gray-500 ml-1">({item.unit})</span> : null}
        </h4>
        <span className="text-[11px] text-gray-500 font-mono">
          real μ={item.real_mean} σ={item.real_std}
          <span className="mx-2 text-gray-300">|</span>
          synth μ={item.synth_mean} σ={item.synth_std}
        </span>
      </div>
      <div className="h-56 w-full">
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
              labelFormatter={(label) => `${item.label}: ${label}`}
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

function CategoricalBar({ item }: { item: CategoricalDistributionItem }) {
  const data = item.categories.map((c) => ({
    name: c.name,
    real: Math.round(c.real_pct * 1000) / 10,
    synth: Math.round(c.synth_pct * 1000) / 10,
  }));
  return (
    <div className="mb-4 last:mb-0">
      <div className="flex items-baseline justify-between mb-1">
        <h4 className="text-sm font-semibold text-gray-700">
          {item.label}
          {item.total_categories && item.total_categories > item.categories.length ? (
            <span className="text-[11px] font-normal text-gray-500 ml-2">
              （上位 {item.categories.length} / 全 {item.total_categories} カテゴリ）
            </span>
          ) : null}
        </h4>
        <span className="text-[11px] text-gray-500 font-mono">単位: %</span>
      </div>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 8, right: 16, left: 32, bottom: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis type="number" tick={{ fontSize: 10, fill: "#6b7280" }} />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 11, fill: "#374151" }}
              width={100}
            />
            <Tooltip
              contentStyle={{ fontSize: 12 }}
              formatter={(value) => (typeof value === "number" ? `${value.toFixed(1)}%` : value)}
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

function ItemRenderer({ item }: { item: DistributionItem }) {
  if (item.type === "numeric") return <NumericHistogram item={item} />;
  return <CategoricalBar item={item} />;
}

export function DistributionComparisonChart({ caseId }: { caseId: string }) {
  const { data, loading, error } = useDistributionData(caseId);

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          分布比較
        </h2>
        <p className="text-sm text-gray-400">分布データを読み込み中...</p>
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
          分布比較
        </h2>
        <p className="text-xs text-gray-500 mt-1 leading-relaxed">
          元データ（青）と合成データ（橙）の分布を比較。合成は <span className="font-mono">{data.selected_synth.library} / {data.selected_synth.algorithm}</span>（{data.synth_source.rows.toLocaleString()} 行）、real は {data.real_source.rows.toLocaleString()} 行から抽出。
        </p>
      </div>
      {data.items.map((it) => (
        <ItemRenderer key={`${it.type}-${it.column}`} item={it} />
      ))}
      <p className="text-[11px] text-gray-400 leading-relaxed mt-3">{data.note}</p>
    </div>
  );
}
