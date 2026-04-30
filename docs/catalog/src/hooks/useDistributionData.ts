import { useEffect, useState } from "react";
import type { DistributionData } from "../types/distribution";

type State = {
  data: DistributionData | null;
  loading: boolean;
  error: string | null;
};

export function useDistributionData(caseId: string | undefined): State {
  const [state, setState] = useState<State>({ data: null, loading: !!caseId, error: null });

  useEffect(() => {
    if (!caseId) {
      setState({ data: null, loading: false, error: null });
      return;
    }
    let cancelled = false;
    setState({ data: null, loading: true, error: null });

    const url = `${import.meta.env.BASE_URL}data/distribution/${caseId}.json`;
    fetch(url)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        return res.json() as Promise<DistributionData>;
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
