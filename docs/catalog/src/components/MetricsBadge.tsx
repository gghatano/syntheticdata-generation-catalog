import type { PrivacyRiskLevel } from "../types/algorithm";
import { PRIVACY_RISK_LABELS } from "../constants/categories";

type MetricsBadgeProps = {
  level: PrivacyRiskLevel;
};

const colorClasses: Record<string, string> = {
  green: "bg-green-100 text-green-800",
  yellow: "bg-yellow-100 text-yellow-800",
  red: "bg-red-100 text-red-800",
};

export function MetricsBadge({ level }: MetricsBadgeProps) {
  const info = PRIVACY_RISK_LABELS[level];
  const cls = colorClasses[info.color] ?? "bg-gray-100 text-gray-800";

  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {info.label}
    </span>
  );
}
