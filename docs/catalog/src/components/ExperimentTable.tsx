import type { Experiment } from "../types/algorithm";

type ExperimentTableProps = {
  experiments: Experiment[];
};

export function ExperimentTable({ experiments }: ExperimentTableProps) {
  if (experiments.length === 0) {
    return <p className="text-gray-500 text-sm">実験データがありません。</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="px-3 py-2 font-semibold">Library</th>
            <th className="px-3 py-2 font-semibold">Dataset</th>
            <th className="px-3 py-2 font-semibold">Phase</th>
            <th className="px-3 py-2 font-semibold">Params</th>
            <th className="px-3 py-2 font-semibold text-right">Quality</th>
            <th className="px-3 py-2 font-semibold text-right">TSTR F1</th>
            <th className="px-3 py-2 font-semibold text-right">DCR Mean</th>
            <th className="px-3 py-2 font-semibold text-right">Time(s)</th>
          </tr>
        </thead>
        <tbody>
          {experiments.map((exp, i) => (
            <tr
              key={exp.id}
              className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}
            >
              <td className="px-3 py-2">
                {exp.library}
                {exp.library_version && (
                  <span className="text-gray-400 ml-1 text-xs">v{exp.library_version}</span>
                )}
              </td>
              <td className="px-3 py-2">{exp.dataset}</td>
              <td className="px-3 py-2">{exp.phase}</td>
              <td className="px-3 py-2 text-xs text-gray-600 max-w-48 truncate">
                {Object.entries(exp.params)
                  .map(([k, v]) => `${k}=${v}`)
                  .join(", ") || "-"}
              </td>
              <td className="px-3 py-2 text-right">{exp.metrics.quality_score?.toFixed(3) ?? "-"}</td>
              <td className="px-3 py-2 text-right">{exp.metrics.tstr_f1?.toFixed(3) ?? "-"}</td>
              <td className="px-3 py-2 text-right">{exp.metrics.dcr_mean?.toFixed(3) ?? "-"}</td>
              <td className="px-3 py-2 text-right">{exp.metrics.time_sec?.toFixed(1) ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
