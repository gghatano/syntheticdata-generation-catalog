import type { PrivacyRiskLevel } from "../types/algorithm";
import { PRIVACY_RISK_LABELS } from "../constants/categories";

type MetricsBadgeProps = {
  level: PrivacyRiskLevel;
};

const colorClasses: Record<string, string> = {
  green: "bg-green-100 text-green-800 border border-green-300",
  yellow: "bg-yellow-100 text-yellow-800 border border-yellow-300",
  red: "bg-red-100 text-red-800 border border-red-300",
};

const dotClasses: Record<string, string> = {
  green: "bg-green-500",
  yellow: "bg-yellow-500",
  red: "bg-red-500",
};

export function MetricsBadge({ level }: MetricsBadgeProps) {
  const info = PRIVACY_RISK_LABELS[level];
  const cls = colorClasses[info.color] ?? "bg-gray-100 text-gray-800 border border-gray-300";
  const dot = dotClasses[info.color] ?? "bg-gray-500";

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${cls}`}>
      <span className={`inline-block w-2 h-2 rounded-full ${dot}`} />
      {info.label}
    </span>
  );
}
