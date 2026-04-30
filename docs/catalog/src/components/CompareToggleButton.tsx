import { useCompareSelection } from "../hooks/useCompareSelection";

export function CompareToggleButton({
  algorithmId,
  algorithmName,
}: {
  algorithmId: string;
  algorithmName: string;
}) {
  const { has, toggle, isFull } = useCompareSelection();
  const checked = has(algorithmId);
  const disabled = !checked && isFull;

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    toggle(algorithmId);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      aria-pressed={checked}
      aria-label={
        checked
          ? `${algorithmName} を比較対象から外す`
          : `${algorithmName} を比較対象に追加`
      }
      title={
        disabled
          ? "比較対象は最大 3 件まで"
          : checked
          ? "比較対象から外す"
          : "比較対象に追加"
      }
      className={
        "inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border transition-colors " +
        (checked
          ? "bg-blue-600 text-white border-blue-600 hover:bg-blue-700"
          : disabled
          ? "bg-gray-50 text-gray-400 border-gray-200 cursor-not-allowed"
          : "bg-white text-gray-600 border-gray-300 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300")
      }
    >
      <svg
        className="w-3.5 h-3.5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        {checked ? (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        ) : (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        )}
      </svg>
      {checked ? "比較中" : "比較に追加"}
    </button>
  );
}
