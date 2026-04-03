import { useState } from "react";
import { useAlgorithms } from "../hooks/useAlgorithms";
import { useFilter } from "../hooks/useFilter";
import { FilterPanel } from "../components/FilterPanel";
import { AlgorithmCard } from "../components/AlgorithmCard";
import { BeginnerGuide } from "../components/BeginnerGuide";

export function ListPage() {
  const { algorithms, loading, error } = useAlgorithms();
  const {
    filters,
    filtered,
    availableLibraries,
    availableUseCases,
    availableInputRequirements,
    toggleCategory,
    toggleDataType,
    toggleLibrary,
    toggleUseCase,
    toggleInputRequirement,
    setSearchQuery,
    setSortBy,
    clearFilters,
    hasActiveFilters,
  } = useFilter(algorithms);

  const [drawerOpen, setDrawerOpen] = useState(false);

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

  const filterPanelProps = {
    filters,
    availableLibraries,
    availableUseCases,
    availableInputRequirements,
    totalCount: algorithms.length,
    filteredCount: filtered.length,
    hasActiveFilters,
    onToggleCategory: toggleCategory,
    onToggleDataType: toggleDataType,
    onToggleLibrary: toggleLibrary,
    onToggleUseCase: toggleUseCase,
    onToggleInputRequirement: toggleInputRequirement,
    onSearchChange: setSearchQuery,
    onSortChange: setSortBy,
    onClearFilters: clearFilters,
  };

  return (
    <div>
      {/* Mobile filter button */}
      <div className="md:hidden mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-600">
          <span className="font-bold text-gray-800">{filtered.length}</span>
          <span className="text-gray-400"> / {algorithms.length} 件</span>
        </p>
        <button
          onClick={() => setDrawerOpen(true)}
          className="inline-flex items-center gap-1.5 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          フィルタ
          {hasActiveFilters && (
            <span className="inline-flex items-center justify-center w-5 h-5 bg-blue-600 text-white text-xs rounded-full">
              !
            </span>
          )}
        </button>
      </div>

      {/* Mobile search / sort */}
      <div className="md:hidden mb-4 space-y-2">
        <input
          type="text"
          value={filters.searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="名前・タグで検索..."
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={filters.sortBy}
          onChange={(e) => setSortBy(e.target.value as typeof filters.sortBy)}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="quality">品質スコア</option>
          <option value="tstr">TSTR F1</option>
          <option value="dcr">DCR Mean</option>
          <option value="time">実行時間</option>
        </select>
      </div>

      {/* Mobile filter drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/40 transition-opacity"
            onClick={() => setDrawerOpen(false)}
          />
          {/* Drawer */}
          <div className="absolute inset-y-0 left-0 w-80 max-w-[85vw] bg-gray-50 shadow-xl overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
              <h2 className="font-bold text-gray-800">フィルタ</h2>
              <button
                onClick={() => setDrawerOpen(false)}
                className="p-1 rounded hover:bg-gray-100 transition-colors"
              >
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-4">
              <FilterPanel {...filterPanelProps} mobile />
            </div>
          </div>
        </div>
      )}

      {/* Beginner guide */}
      <BeginnerGuide />

      <div className="flex gap-6">
        {/* Desktop filter panel */}
        <FilterPanel {...filterPanelProps} />

        <div className="flex-1 min-w-0">
          {/* Summary header (desktop) */}
          <div className="hidden md:flex items-center justify-between mb-4">
            <p className="text-sm text-gray-500">
              <span className="font-semibold text-gray-700">{filtered.length}</span> 件のアルゴリズムが見つかりました
              {hasActiveFilters && (
                <span className="text-gray-400"> ({algorithms.length} 件中)</span>
              )}
            </p>
          </div>

          {/* Card grid: 1 col mobile, 2 col tablet, 3 col desktop */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((algo) => (
              <AlgorithmCard key={algo.id} algorithm={algo} />
            ))}
          </div>

          {filtered.length === 0 && (
            <div className="text-center py-16">
              <p className="text-gray-400 mb-3">条件に一致するアルゴリズムがありません。</p>
              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
                >
                  フィルタをクリア
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
