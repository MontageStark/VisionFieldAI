import { useEffect, useState, useCallback } from 'react';
import { streamApi } from '@/services/api';
import { wsClient } from '@/services/websocket';
import type { StreamStatus, WebSocketMessage } from '@/types/api';

function LoadingSpinner({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-400">
      <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      {label}
    </div>
  );
}

export default function Streaming(): JSX.Element {
  const [status, setStatus] = useState<StreamStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<'start' | 'stop' | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await streamApi.status();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stream status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const poll = setInterval(fetchStatus, 2000);
    return () => clearInterval(poll);
  }, [fetchStatus]);

  useEffect(() => {
    const unsubMsg = wsClient.onMessage((msg: WebSocketMessage) => {
      if (msg.type === 'stream_update' && msg.message) {
        try {
          setStatus(JSON.parse(msg.message));
        } catch { /* ignore */ }
      }
    });
    return () => { unsubMsg(); };
  }, []);

  const handleStart = async () => {
    setActionLoading('start');
    try {
      await streamApi.start();
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start stream');
    } finally {
      setActionLoading(null);
    }
  };

  const handleStop = async () => {
    setActionLoading('stop');
    try {
      await streamApi.stop();
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop stream');
    } finally {
      setActionLoading(null);
    }
  };

  const isActive = status?.active ?? false;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Streaming</h1>
        <button
          onClick={fetchStatus}
          className="flex items-center gap-2 rounded-md bg-slate-700 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-600 transition-colors"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-md bg-rose-500/10 border border-rose-500/30 p-3 text-sm text-rose-400">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">Status</p>
          <div className="mt-2 flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${isActive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
            <p className={`font-mono text-xl ${isActive ? 'text-emerald-400' : 'text-slate-400'}`}>
              {isActive ? 'Active' : 'Inactive'}
            </p>
          </div>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">FPS</p>
          <p className="mt-2 font-mono text-3xl text-white">
            {status?.fps?.toFixed(1) ?? '—'}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">Bitrate</p>
          <p className="mt-2 font-mono text-3xl text-white">
            {status?.bitrate_kbps ?? '—'}<span className="text-sm text-slate-400"> kbps</span>
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">URL</p>
          <p className="mt-2 font-mono text-sm text-slate-300 truncate">
            {status?.url ?? '—'}
          </p>
        </div>
      </div>

      <section className="card">
        <h2 className="text-base font-semibold text-white">Stream Control</h2>
        <p className="mt-1 text-sm text-slate-400">
          Start or stop the streaming pipeline.
        </p>
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={handleStart}
            disabled={actionLoading !== null || isActive}
            className="flex items-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {actionLoading === 'start' ? <LoadingSpinner label="Starting..." /> : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Start Stream
              </>
            )}
          </button>
          <button
            onClick={handleStop}
            disabled={actionLoading !== null || !isActive}
            className="flex items-center gap-2 rounded-md bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {actionLoading === 'stop' ? <LoadingSpinner label="Stopping..." /> : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                </svg>
                Stop Stream
              </>
            )}
          </button>
        </div>
      </section>

      <section className="card">
        <h2 className="text-base font-semibold text-white">Stream Details</h2>
        <p className="mt-1 text-sm text-slate-400">
          Current stream configuration and metrics.
        </p>
        <div className="mt-4">
          {loading ? (
            <LoadingSpinner label="Loading stream details..." />
          ) : status ? (
            <pre className="overflow-x-auto rounded-md bg-slate-800 p-3 text-xs text-slate-300">
              {JSON.stringify(status, null, 2)}
            </pre>
          ) : (
            <p className="text-sm text-slate-500">No stream status available.</p>
          )}
        </div>
      </section>
    </div>
  );
}