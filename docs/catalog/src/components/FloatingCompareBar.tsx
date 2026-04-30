import { Link } from "react-router-dom";
import { useCompareSelection } from "../hooks/useCompareSelection";
import { useAlgorithms } from "../hooks/useAlgorithms";

export function FloatingCompareBar() {
  const { selected, remove, clear, max } = useCompareSelection();
  const { algorithms } = useAlgorithms();

  if (selected.length === 0) return null;

  const idToName = new Map(algorithms.map((a) => [a.id, a.name]));

  const compareHref = `/compare?ids=${selected.join(",")}`;
  const canCompare = selected.length >= 2;

  return (
    <div
      role="region"
      aria-label="比較対象選択中"
      className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 max-w-3xl w-[calc(100%-2rem)]"
    >
      <div className="bg-white border border-gray-200 rounded-2xl shadow-2xl px-4 py-3 flex items-center gap-3">
        <span className="text-sm font-semibold text-gray-700 shrink-0">
          {selected.length}/{max} 件選択中
        </span>

        <div className="flex-1 flex flex-wrap gap-1.5 min-w-0">
          {selected.map((id) => (
            <span
              key={id}
              className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 text-xs font-medium px-2 py-0.5 rounded-full border border-blue-200"
            >
              {idToName.get(id) ?? id}
              <button
                type="button"
                onClick={() => remove(id)}
                aria-label={`${idToName.get(id) ?? id} を比較対象から外す`}
                className="hover:text-blue-900"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          ))}
        </div>

        <button
          type="button"
          onClick={clear}
          className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 shrink-0"
        >
          すべてクリア
        </button>

        <Link
          to={compareHref}
          aria-disabled={!canCompare}
          onClick={(e) => {
            if (!canCompare) e.preventDefault();
          }}
          className={
            "inline-flex items-center gap-1 px-4 py-2 rounded-full text-sm font-semibold shrink-0 " +
            (canCompare
              ? "bg-blue-600 text-white hover:bg-blue-700"
              : "bg-gray-200 text-gray-400 cursor-not-allowed")
          }
          title={canCompare ? "比較ページへ" : "2件以上を選択してください"}
        >
          比較する
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </div>
    </div>
  );
}
