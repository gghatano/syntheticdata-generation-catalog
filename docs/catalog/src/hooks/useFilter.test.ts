import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useFilter } from "./useFilter";
import { mockAlgorithms } from "../test/fixtures";

describe("useFilter", () => {
  it("returns all algorithms when no filters are active", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    expect(result.current.filtered).toHaveLength(3);
    expect(result.current.hasActiveFilters).toBe(false);
  });

  it("filters by category", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => result.current.toggleCategory("gan"));
    expect(result.current.filtered).toHaveLength(1);
    expect(result.current.filtered[0].id).toBe("ctgan");
    expect(result.current.hasActiveFilters).toBe(true);
  });

  it("filters by multiple categories (OR logic)", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => {
      result.current.toggleCategory("gan");
      result.current.toggleCategory("copula");
    });
    expect(result.current.filtered).toHaveLength(2);
  });

  it("toggles category off when clicked again", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => result.current.toggleCategory("gan"));
    expect(result.current.filtered).toHaveLength(1);
    act(() => result.current.toggleCategory("gan"));
    expect(result.current.filtered).toHaveLength(3);
  });

  it("filters by library", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => result.current.toggleLibrary("SynthCity"));
    expect(result.current.filtered).toHaveLength(2); // ctgan + bayesian_network
  });

  it("filters by supported_data", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    // all mock data is single_table
    act(() => result.current.toggleDataType("multi_table"));
    expect(result.current.filtered).toHaveLength(0);
  });

  it("filters by use_cases", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => result.current.toggleUseCase("マスターデータ匿名化"));
    expect(result.current.filtered).toHaveLength(1);
    expect(result.current.filtered[0].id).toBe("ctgan");
  });

  it("filters by input_requirements", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => result.current.toggleInputRequirement("欠損値対応"));
    expect(result.current.filtered).toHaveLength(2); // gaussiancopula + bayesian_network
  });

  it("filters by search query (name)", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => result.current.setSearchQuery("copula"));
    expect(result.current.filtered).toHaveLength(1);
    expect(result.current.filtered[0].id).toBe("gaussiancopula");
  });

  it("filters by search query (tag)", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => result.current.setSearchQuery("深層学習"));
    expect(result.current.filtered).toHaveLength(1);
    expect(result.current.filtered[0].id).toBe("ctgan");
  });

  it("search is case insensitive", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => result.current.setSearchQuery("CTGAN"));
    expect(result.current.filtered).toHaveLength(1);
  });

  it("combines multiple filters (AND logic between filter types)", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => {
      result.current.toggleCategory("gan");
      result.current.toggleLibrary("SDV");
    });
    expect(result.current.filtered).toHaveLength(1);
    expect(result.current.filtered[0].id).toBe("ctgan");
  });

  it("sorts by quality score descending", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => result.current.setSortBy("quality"));
    expect(result.current.filtered[0].id).toBe("ctgan"); // 0.86
    expect(result.current.filtered[1].id).toBe("bayesian_network"); // 0.8263
    expect(result.current.filtered[2].id).toBe("gaussiancopula"); // 0.8168
  });

  it("sorts by tstr f1 descending", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => result.current.setSortBy("tstr"));
    expect(result.current.filtered[0].id).toBe("bayesian_network"); // 0.8591
  });

  it("sorts by dcr descending (higher = safer)", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => result.current.setSortBy("dcr"));
    expect(result.current.filtered[0].id).toBe("gaussiancopula"); // 0.533
  });

  it("sorts by time ascending (faster first)", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => result.current.setSortBy("time"));
    expect(result.current.filtered[0].id).toBe("gaussiancopula"); // 5.94
  });

  it("clearFilters resets all filters", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    act(() => {
      result.current.toggleCategory("gan");
      result.current.setSearchQuery("test");
      result.current.toggleLibrary("SDV");
    });
    expect(result.current.hasActiveFilters).toBe(true);
    act(() => result.current.clearFilters());
    expect(result.current.hasActiveFilters).toBe(false);
    expect(result.current.filtered).toHaveLength(3);
  });

  it("extracts available libraries from data", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    expect(result.current.availableLibraries).toEqual(["SDV", "SynthCity", "ydata"]);
  });

  it("extracts available use cases from data", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    expect(result.current.availableUseCases).toContain("テストデータ生成");
    expect(result.current.availableUseCases).toContain("マスターデータ匿名化");
  });

  it("extracts available input requirements from data", () => {
    const { result } = renderHook(() => useFilter(mockAlgorithms));
    expect(result.current.availableInputRequirements).toContain("カテゴリ対応");
    expect(result.current.availableInputRequirements).toContain("欠損値対応");
  });
});
