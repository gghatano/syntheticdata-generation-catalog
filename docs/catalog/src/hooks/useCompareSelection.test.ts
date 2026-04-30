import { describe, it, expect, beforeEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useCompareSelection } from "./useCompareSelection";

beforeEach(() => {
  localStorage.clear();
});

describe("useCompareSelection", () => {
  it("(a) toggle で 1 件追加され has が true になる", () => {
    const { result } = renderHook(() => useCompareSelection());
    expect(result.current.selected).toEqual([]);

    act(() => result.current.toggle("ctgan"));
    expect(result.current.selected).toEqual(["ctgan"]);
    expect(result.current.has("ctgan")).toBe(true);
  });

  it("(b) toggle で同じ id を 2 回押すと外れる", () => {
    const { result } = renderHook(() => useCompareSelection());
    act(() => result.current.toggle("ctgan"));
    act(() => result.current.toggle("ctgan"));
    expect(result.current.selected).toEqual([]);
    expect(result.current.has("ctgan")).toBe(false);
  });

  it("(c) 最大 3 件まで。4 件目は無視される", () => {
    const { result } = renderHook(() => useCompareSelection());
    act(() => {
      result.current.toggle("a");
      result.current.toggle("b");
      result.current.toggle("c");
      result.current.toggle("d");
    });
    expect(result.current.selected).toEqual(["a", "b", "c"]);
    expect(result.current.isFull).toBe(true);
  });

  it("(d) localStorage に永続化され、再 mount で復元される", () => {
    const { result, unmount } = renderHook(() => useCompareSelection());
    act(() => result.current.toggle("ctgan"));
    act(() => result.current.toggle("tvae"));
    unmount();

    const { result: result2 } = renderHook(() => useCompareSelection());
    expect(result2.current.selected).toEqual(["ctgan", "tvae"]);
  });

  it("(e) clear ですべて空になる", () => {
    const { result } = renderHook(() => useCompareSelection());
    act(() => {
      result.current.toggle("a");
      result.current.toggle("b");
    });
    act(() => result.current.clear());
    expect(result.current.selected).toEqual([]);
  });

  it("(f) remove で指定 id だけ外れる", () => {
    const { result } = renderHook(() => useCompareSelection());
    act(() => {
      result.current.toggle("a");
      result.current.toggle("b");
    });
    act(() => result.current.remove("a"));
    expect(result.current.selected).toEqual(["b"]);
  });
});
