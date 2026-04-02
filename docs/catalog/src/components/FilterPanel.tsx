import type { AlgorithmCategory, DataType } from "../types/algorithm";
import type { FilterState, SortBy } from "../hooks/useFilter";
import { CATEGORY_LABELS, DATA_TYPE_LABELS } from "../constants/categories";

type FilterPanelProps = {
  filters: FilterState;
  availableLibraries: string[];
  onToggleCategory: (cat: AlgorithmCategory) => void;
  onToggleDataType: (dt: DataType) => void;
  onToggleLibrary: (lib: string) => void;
  onSearchChange: (query: string) => void;
  onSortChange: (sort: SortBy) => void;
};

export function FilterPanel({
  filters,
  availableLibraries,
  onToggleCategory,
  onToggleDataType,
  onToggleLibrary,
  onSearchChange,
  onSortChange,
}: FilterPanelProps) {
  return (
    <aside className="w-64 shrink-0 hidden md:block">
      <div className="bg-white rounded-lg shadow p-4 space-y-6">
        {/* Search */}
        <div>
          <label className="block text-sm font-semibold mb-1">検索</label>
          <input
            type="text"
            value={filters.searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="名前・タグで検索..."
            className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Sort */}
        <div>
          <label className="block text-sm font-semibold mb-1">ソート</label>
          <select
            value={filters.sortBy}
            onChange={(e) => onSortChange(e.target.value as SortBy)}
            className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="quality">品質スコア</option>
            <option value="tstr">TSTR F1</option>
            <option value="dcr">DCR Mean</option>
            <option value="time">実行時間</option>
          </select>
        </div>

        {/* Category */}
        <div>
          <h3 className="text-sm font-semibold mb-2">カテゴリ</h3>
          <div className="space-y-1">
            {(Object.entries(CATEGORY_LABELS) as [AlgorithmCategory, string][]).map(
              ([key, label]) => (
                <label key={key} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.category.includes(key)}
                    onChange={() => onToggleCategory(key)}
                    className="rounded"
                  />
                  {label}
                </label>
              )
            )}
          </div>
        </div>

        {/* Data Type */}
        <div>
          <h3 className="text-sm font-semibold mb-2">データタイプ</h3>
          <div className="space-y-1">
            {(Object.entries(DATA_TYPE_LABELS) as [DataType, string][]).map(
              ([key, label]) => (
                <label key={key} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.supported_data.includes(key)}
                    onChange={() => onToggleDataType(key)}
                    className="rounded"
                  />
                  {label}
                </label>
              )
            )}
          </div>
        </div>

        {/* Libraries */}
        {availableLibraries.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-2">ライブラリ</h3>
            <div className="space-y-1">
              {availableLibraries.map((lib) => (
                <label key={lib} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.libraries.includes(lib)}
                    onChange={() => onToggleLibrary(lib)}
                    className="rounded"
                  />
                  {lib}
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
