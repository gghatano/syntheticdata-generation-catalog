import { useAlgorithms } from "../hooks/useAlgorithms";
import { useFilter } from "../hooks/useFilter";
import { FilterPanel } from "../components/FilterPanel";
import { AlgorithmCard } from "../components/AlgorithmCard";

export function ListPage() {
  const { algorithms, loading, error } = useAlgorithms();
  const {
    filters,
    filtered,
    availableLibraries,
    toggleCategory,
    toggleDataType,
    toggleLibrary,
    setSearchQuery,
    setSortBy,
  } = useFilter(algorithms);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <span className="text-gray-500">読み込み中...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center py-20">
        <span className="text-red-500">エラー: {error}</span>
      </div>
    );
  }

  return (
    <div className="flex gap-6">
      <FilterPanel
        filters={filters}
        availableLibraries={availableLibraries}
        onToggleCategory={toggleCategory}
        onToggleDataType={toggleDataType}
        onToggleLibrary={toggleLibrary}
        onSearchChange={setSearchQuery}
        onSortChange={setSortBy}
      />

      <div className="flex-1 min-w-0">
        {/* Mobile search / sort (visible on small screens) */}
        <div className="md:hidden mb-4 space-y-2">
          <input
            type="text"
            value={filters.searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="検索..."
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          <select
            value={filters.sortBy}
            onChange={(e) => setSortBy(e.target.value as typeof filters.sortBy)}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          >
            <option value="quality">品質スコア</option>
            <option value="tstr">TSTR F1</option>
            <option value="dcr">DCR Mean</option>
            <option value="time">実行時間</option>
          </select>
        </div>

        <p className="text-sm text-gray-500 mb-4">
          {filtered.length} 件のアルゴリズム
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filtered.map((algo) => (
            <AlgorithmCard key={algo.id} algorithm={algo} />
          ))}
        </div>

        {filtered.length === 0 && (
          <p className="text-center text-gray-400 py-10">
            条件に一致するアルゴリズムがありません。
          </p>
        )}
      </div>
    </div>
  );
}
