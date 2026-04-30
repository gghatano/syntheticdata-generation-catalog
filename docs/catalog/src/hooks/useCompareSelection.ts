import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "syntheticdata-catalog-compare-selection";
const MAX_SELECTION = 3;

function readStorage(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((x): x is string => typeof x === "string").slice(0, MAX_SELECTION);
  } catch {
    return [];
  }
}

function writeStorage(ids: string[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  } catch {
    // localStorage が使えない環境（SSR・Privacy mode など）は無視
  }
}

/**
 * 比較選択中アルゴリズムの状態を localStorage と同期する。
 * 最大 3 件。すでに含まれていれば toggle で外す。
 */
export function useCompareSelection() {
  const [selected, setSelected] = useState<string[]>(() => readStorage());

  useEffect(() => {
    writeStorage(selected);
  }, [selected]);

  // 別タブで storage が更新された場合の同期
  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        setSelected(readStorage());
      }
    };
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);

  const toggle = useCallback((id: string) => {
    setSelected((cur) => {
      if (cur.includes(id)) return cur.filter((x) => x !== id);
      if (cur.length >= MAX_SELECTION) return cur;
      return [...cur, id];
    });
  }, []);

  const remove = useCallback((id: string) => {
    setSelected((cur) => cur.filter((x) => x !== id));
  }, []);

  const clear = useCallback(() => {
    setSelected([]);
  }, []);

  const has = useCallback((id: string) => selected.includes(id), [selected]);

  const isFull = selected.length >= MAX_SELECTION;

  return { selected, toggle, remove, clear, has, isFull, max: MAX_SELECTION };
}
