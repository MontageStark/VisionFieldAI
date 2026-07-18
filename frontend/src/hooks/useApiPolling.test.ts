import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useApiPolling } from '@/hooks/useApiPolling';

describe('useApiPolling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('calls the fetcher immediately on mount', async () => {
    const fetcher = vi.fn().mockResolvedValue({ data: 'test' });
    renderHook(() => useApiPolling(fetcher, 1000));
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it('returns loading state initially', () => {
    const fetcher = vi.fn().mockResolvedValue({ data: 'test' });
    const { result } = renderHook(() => useApiPolling(fetcher, 1000));
    expect(result.current.loading).toBe(true);
  });

  it('returns data after fetch completes', async () => {
    const fetcher = vi.fn().mockResolvedValue({ data: 'test' });
    const { result } = renderHook(() => useApiPolling(fetcher, 1000));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual({ data: 'test' });
  });

  it('returns error when fetch fails', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('Network error'));
    const { result } = renderHook(() => useApiPolling(fetcher, 1000));
    await waitFor(() => expect(result.current.error).toBe('Network error'));
  });

  it('polls at the specified interval', async () => {
    const fetcher = vi.fn().mockResolvedValue({ data: 'test' });
    renderHook(() => useApiPolling(fetcher, 5000));
    expect(fetcher).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(5000);
    expect(fetcher).toHaveBeenCalledTimes(2);
    vi.advanceTimersByTime(5000);
    expect(fetcher).toHaveBeenCalledTimes(3);
  });

  it('stops polling when enabled is false', async () => {
    const fetcher = vi.fn().mockResolvedValue({ data: 'test' });
    renderHook(() => useApiPolling(fetcher, 5000, { enabled: false }));
    expect(fetcher).not.toHaveBeenCalled();
  });

  it('refetch calls fetcher manually', async () => {
    const fetcher = vi.fn().mockResolvedValue({ data: 'test' });
    const { result } = renderHook(() => useApiPolling(fetcher, 5000));
    await waitFor(() => expect(result.current.loading).toBe(false));
    fetcher.mockClear();
    await act(async () => {
      await result.current.refetch();
    });
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual({ data: 'test' });
  });

  it('refetch handles errors', async () => {
    const fetcher = vi.fn().mockResolvedValue({ data: 'ok' });
    const { result } = renderHook(() => useApiPolling(fetcher, 5000));
    await waitFor(() => expect(result.current.loading).toBe(false));
    fetcher.mockRejectedValue(new Error('Refetch fail'));
    await act(async () => {
      await result.current.refetch();
    });
    expect(result.current.error).toBe('Refetch fail');
  });

  it('returns string error for non-Error rejections', async () => {
    const fetcher = vi.fn().mockRejectedValue('string error');
    const { result } = renderHook(() => useApiPolling(fetcher, 1000));
    await waitFor(() => expect(result.current.error).toBe('string error'));
  });
});
