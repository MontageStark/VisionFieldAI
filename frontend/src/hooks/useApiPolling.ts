import { useState, useEffect, useRef, useCallback } from 'react';

interface UseApiPollingOptions {
  interval?: number;
  enabled?: boolean;
}

export function useApiPolling<T>(
  fetcher: () => Promise<T>,
  interval: number = 3000,
  options?: UseApiPollingOptions,
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const fetcherRef = useRef(fetcher);
  const enabled = options?.enabled !== false;

  useEffect(() => {
    fetcherRef.current = fetcher;
  }, [fetcher]);

  const refetch = useCallback(async () => {
    try {
      const result = await fetcherRef.current();
      setData(result);
      setError(null);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;

    const poll = async () => {
      try {
        const result = await fetcherRef.current();
        if (!cancelled) {
          setData(result);
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)));
          setLoading(false);
        }
      }
    };

    poll();
    const id = setInterval(poll, interval);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [interval, enabled]);

  return { data, error, loading, refetch };
}
