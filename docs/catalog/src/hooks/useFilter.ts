import { useState, useMemo } from "react";
import type { Algorithm, AlgorithmCategory, DataType } from "../types/algorithm";

export type SortBy = "quality" | "tstr" | "dcr" | "time";

export type FilterState = {
  category: AlgorithmCategory[];
  supported_data: DataType[];
  libraries: string[];
  use_cases: string[];
  input_requirements: string[];
  searchQuery: string;
  sortBy: SortBy;
};

export function useFilter(algorithms: Algorithm[]) {
  const [filters, setFilters] = useState<FilterState>({
    category: [],
    supported_data: [],
    libraries: [],
    use_cases: [],
    input_requirements: [],
    searchQuery: "",
    sortBy: "quality",
  });

  const availableLibraries = useMemo(() => {
    const libs = new Set<string>();
    algorithms.forEach((a) => a.libraries.forEach((l) => libs.add(l)));
    return Array.from(libs).sort();
  }, [algorithms]);

  const availableUseCases = useMemo(() => {
    const cases = new Set<string>();
    algorithms.forEach((a) => a.use_cases.forEach((uc) => cases.add(uc)));
    return Array.from(cases).sort();
  }, [algorithms]);

  const availableInputRequirements = useMemo(() => {
    const reqs = new Set<string>();
    algorithms.forEach((a) => a.input_requirements.forEach((r) => reqs.add(r)));
    return Array.from(reqs).sort();
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
    if (filters.use_cases.length > 0) {
      result = result.filter((a) =>
        a.use_cases.some((uc) => filters.use_cases.includes(uc))
      );
    }
    if (filters.input_requirements.length > 0) {
      result = result.filter((a) =>
        a.input_requirements.some((r) => filters.input_requirements.includes(r))
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

  const toggleUseCase = (uc: string) => {
    setFilters((prev) => ({
      ...prev,
      use_cases: prev.use_cases.includes(uc)
        ? prev.use_cases.filter((u) => u !== uc)
        : [...prev.use_cases, uc],
    }));
  };

  const toggleInputRequirement = (req: string) => {
    setFilters((prev) => ({
      ...prev,
      input_requirements: prev.input_requirements.includes(req)
        ? prev.input_requirements.filter((r) => r !== req)
        : [...prev.input_requirements, req],
    }));
  };

  const setSearchQuery = (searchQuery: string) => {
    setFilters((prev) => ({ ...prev, searchQuery }));
  };

  const setSortBy = (sortBy: SortBy) => {
    setFilters((prev) => ({ ...prev, sortBy }));
  };

  const clearFilters = () => {
    setFilters({
      category: [],
      supported_data: [],
      libraries: [],
      use_cases: [],
      input_requirements: [],
      searchQuery: "",
      sortBy: "quality",
    });
  };

  const hasActiveFilters =
    filters.category.length > 0 ||
    filters.supported_data.length > 0 ||
    filters.libraries.length > 0 ||
    filters.use_cases.length > 0 ||
    filters.input_requirements.length > 0 ||
    filters.searchQuery !== "";

  return {
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
  };
}
