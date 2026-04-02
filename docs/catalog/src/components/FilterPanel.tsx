import type { AlgorithmCategory, DataType } from "../types/algorithm";
import type { FilterState, SortBy } from "../hooks/useFilter";
import { CATEGORY_LABELS, DATA_TYPE_LABELS } from "../constants/categories";

type FilterPanelProps = {
  filters: FilterState;
  availableLibraries: string[];
  availableUseCases: string[];
  availableInputRequirements: string[];
  totalCount: number;
  filteredCount: number;
  hasActiveFilters: boolean;
  mobile?: boolean;
  onToggleCategory: (cat: AlgorithmCategory) => void;
  onToggleDataType: (dt: DataType) => void;
  onToggleLibrary: (lib: string) => void;
  onToggleUseCase: (uc: string) => void;
  onToggleInputRequirement: (req: string) => void;
  onSearchChange: (query: string) => void;
  onSortChange: (sort: SortBy) => void;
  onClearFilters: () => void;
};

export function FilterPanel({
  filters,
  availableLibraries,
  availableUseCases,
  availableInputRequirements,
  totalCount,
  filteredCount,
  hasActiveFilters,
  mobile = false,
  onToggleCategory,
  onToggleDataType,
  onToggleLibrary,
  onToggleUseCase,
  onToggleInputRequirement,
  onSearchChange,
  onSortChange,
  onClearFilters,
}: FilterPanelProps) {
  const asideClass = mobile
    ? "w-full"
    : "w-72 shrink-0 hidden md:block";

  return (
    <aside className={asideClass}>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 space-y-5 sticky top-4">
        {/* Result count */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            <span className="font-bold text-gray-800 text-base">{filteredCount}</span>
            <span className="text-gray-400"> / {totalCount} 件</span>
          </p>
          {hasActiveFilters && (
            <button
              onClick={onClearFilters}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium transition-colors"
            >
              クリア
            </button>
          )}
        </div>

        {/* Search */}
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">検索</label>
          <input
            type="text"
            value={filters.searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="名前・タグで検索..."
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
          />
        </div>

        {/* Sort */}
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">ソート</label>
          <select
            value={filters.sortBy}
            onChange={(e) => onSortChange(e.target.value as SortBy)}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
          >
            <option value="quality">品質スコア</option>
            <option value="tstr">TSTR F1</option>
            <option value="dcr">DCR Mean</option>
            <option value="time">実行時間</option>
          </select>
        </div>

        {/* Category */}
        <FilterSection title="カテゴリ">
          {(Object.entries(CATEGORY_LABELS) as [AlgorithmCategory, string][]).map(
            ([key, label]) => (
              <FilterCheckbox
                key={key}
                label={label}
                checked={filters.category.includes(key)}
                onChange={() => onToggleCategory(key)}
              />
            )
          )}
        </FilterSection>

        {/* Data Type */}
        <FilterSection title="データタイプ">
          {(Object.entries(DATA_TYPE_LABELS) as [DataType, string][]).map(
            ([key, label]) => (
              <FilterCheckbox
                key={key}
                label={label}
                checked={filters.supported_data.includes(key)}
                onChange={() => onToggleDataType(key)}
              />
            )
          )}
        </FilterSection>

        {/* Libraries */}
        {availableLibraries.length > 0 && (
          <FilterSection title="ライブラリ">
            {availableLibraries.map((lib) => (
              <FilterCheckbox
                key={lib}
                label={lib}
                checked={filters.libraries.includes(lib)}
                onChange={() => onToggleLibrary(lib)}
              />
            ))}
          </FilterSection>
        )}

        {/* Use Cases */}
        {availableUseCases.length > 0 && (
          <FilterSection title="ユースケース">
            {availableUseCases.map((uc) => (
              <FilterCheckbox
                key={uc}
                label={uc}
                checked={filters.use_cases.includes(uc)}
                onChange={() => onToggleUseCase(uc)}
              />
            ))}
          </FilterSection>
        )}

        {/* Input Requirements */}
        {availableInputRequirements.length > 0 && (
          <FilterSection title="入力要件">
            {availableInputRequirements.map((req) => (
              <FilterCheckbox
                key={req}
                label={req}
                checked={filters.input_requirements.includes(req)}
                onChange={() => onToggleInputRequirement(req)}
              />
            ))}
          </FilterSection>
        )}
      </div>
    </aside>
  );
}

function FilterSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{title}</h3>
      <div className="space-y-1">
        {children}
      </div>
    </div>
  );
}

function FilterCheckbox({ label, checked, onChange }: { label: string; checked: boolean; onChange: () => void }) {
  return (
    <label className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-50 rounded px-1 py-0.5 transition-colors">
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
      />
      <span className="text-gray-700">{label}</span>
    </label>
  );
}
