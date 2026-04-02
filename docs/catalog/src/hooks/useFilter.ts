import { useState, useMemo } from "react";
import type { Algorithm, AlgorithmCategory, DataType } from "../types/algorithm";

export type SortBy = "quality" | "tstr" | "dcr" | "time";

export type FilterState = {
  category: AlgorithmCategory[];
  supported_data: DataType[];
  libraries: string[];
  searchQuery: string;
  sortBy: SortBy;
};

export function useFilter(algorithms: Algorithm[]) {
  const [filters, setFilters] = useState<FilterState>({
    category: [],
    supported_data: [],
    libraries: [],
    searchQuery: "",
    sortBy: "quality",
  });

  const availableLibraries = useMemo(() => {
    const libs = new Set<string>();
    algorithms.forEach((a) => a.libraries.forEach((l) => libs.add(l)));
    return Array.from(libs).sort();
  }, [algorithms]);

  const filtered = useMemo(() => {
    let result = algorithms;

    if (filters.category.length > 0) {
      result = result.filter((a) => filters.category.includes(a.category));
    }
    if (filters.supported_data.length > 0) {
      result = result.filter((a) =>
        a.supported_data.some((d) => filters.supported_data.includes(d))
      );
    }
    if (filters.libraries.length > 0) {
      result = result.filter((a) =>
        a.libraries.some((l) => filters.libraries.includes(l))
      );
    }
    if (filters.searchQuery) {
      const q = filters.searchQuery.toLowerCase();
      result = result.filter(
        (a) =>
          a.name.toLowerCase().includes(q) ||
          a.description.toLowerCase().includes(q) ||
          a.tags.some((t) => t.toLowerCase().includes(q))
      );
    }

    result = [...result].sort((a, b) => {
      const am = a.summary_metrics;
      const bm = b.summary_metrics;
      if (!am && !bm) return 0;
      if (!am) return 1;
      if (!bm) return -1;

      switch (filters.sortBy) {
        case "quality":
          return bm.best_quality_score - am.best_quality_score;
        case "tstr":
          return bm.best_tstr_f1 - am.best_tstr_f1;
        case "dcr":
          return bm.best_dcr_mean - am.best_dcr_mean;
        case "time":
          return am.fastest_time_sec - bm.fastest_time_sec;
        default:
          return 0;
      }
    });

    return result;
  }, [algorithms, filters]);

  const toggleCategory = (cat: AlgorithmCategory) => {
    setFilters((prev) => ({
      ...prev,
      category: prev.category.includes(cat)
        ? prev.category.filter((c) => c !== cat)
        : [...prev.category, cat],
    }));
  };

  const toggleDataType = (dt: DataType) => {
    setFilters((prev) => ({
      ...prev,
      supported_data: prev.supported_data.includes(dt)
        ? prev.supported_data.filter((d) => d !== dt)
        : [...prev.supported_data, dt],
    }));
  };

  const toggleLibrary = (lib: string) => {
    setFilters((prev) => ({
      ...prev,
      libraries: prev.libraries.includes(lib)
        ? prev.libraries.filter((l) => l !== lib)
        : [...prev.libraries, lib],
    }));
  };

  const setSearchQuery = (searchQuery: string) => {
    setFilters((prev) => ({ ...prev, searchQuery }));
  };

  const setSortBy = (sortBy: SortBy) => {
    setFilters((prev) => ({ ...prev, sortBy }));
  };

  return {
    filters,
    filtered,
    availableLibraries,
    toggleCategory,
    toggleDataType,
    toggleLibrary,
    setSearchQuery,
    setSortBy,
  };
}
