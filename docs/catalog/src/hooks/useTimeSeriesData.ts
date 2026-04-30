import { useEffect, useState } from "react";
import type { TimeSeriesData } from "../types/timeseries";

type State = {
  data: TimeSeriesData | null;
  loading: boolean;
  error: string | null;
};

export function useTimeSeriesData(caseId: string | undefined): State {
  const [state, setState] = useState<State>({ data: null, loading: !!caseId, error: null });

  useEffect(() => {
    if (!caseId) {
      setState({ data: null, loading: false, error: null });
      return;
    }
    let cancelled = false;
    setState({ data: null, loading: true, error: null });

    const url = `${import.meta.env.BASE_URL}data/timeseries/${caseId}.json`;
    fetch(url)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        return res.json() as Promise<TimeSeriesData>;
      })
      .then((data) => {
        if (!cancelled) setState({ data, loading: false, error: null });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : "unknown";
          setState({ data: null, loading: false, error: message });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [caseId]);

  return state;
}
