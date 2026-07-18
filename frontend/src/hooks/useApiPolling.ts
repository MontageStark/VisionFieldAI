import { useState, useEffect, useCallback, useRef } from 'react';

interface UseApiPollingOptions {
  enabled?: boolean;
}

export function useApiPolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number = 5000,
  options: UseApiPollingOptions = {}
) {
  const { enabled = true } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetcherRef = useRef(fetcher);

  useEffect(() => {
    fetcherRef.current = fetcher;
  }, [fetcher]);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    const run = async () => {
      try {
        setLoading(true);
        const result = await fetcherRef.current();
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    run();

    const id = setInterval(run, intervalMs);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [enabled, intervalMs]);

  const refetch = useCallback(async () => {
    try {
      setLoading(true);
      const result = await fetcherRef.current();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, refetch };
}

export default useApiPolling;
