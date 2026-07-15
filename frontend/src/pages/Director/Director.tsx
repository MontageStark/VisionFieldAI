import { useEffect, useState, useCallback } from 'react';
import { directorApi } from '@/services/api';
import { wsClient } from '@/services/websocket';
import type { DirectorMode, DirectorStatus, DirectorDecision, WebSocketMessage } from '@/types/api';

const MODES: DirectorMode[] = ['broadcast', 'aggressive', 'wide', 'training', 'manual_assist'];

const MODE_LABELS: Record<DirectorMode, string> = {
  broadcast: 'Broadcast',
  aggressive: 'Aggressive',
  wide: 'Wide',
  training: 'Training',
  manual_assist: 'Manual Assist',
};

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-rose-500';
  return (
    <div className="flex items-center gap-3">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-700">
        <div className={`h-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-12 text-right font-mono text-sm text-white">{pct}%</span>
    </div>
  );
}

export default function Director(): JSX.Element {
  const [status, setStatus] = useState<DirectorStatus | null>(null);
  const [lastDecision, setLastDecision] = useState<DirectorDecision | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<DirectorMode | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await directorApi.status();
      setStatus(data);
      if (data.last_decision) {
        setLastDecision(data.last_decision);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch director status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const poll = setInterval(fetchStatus, 3000);
    return () => clearInterval(poll);
  }, [fetchStatus]);

  useEffect(() => {
    const unsubMsg = wsClient.onMessage((msg: WebSocketMessage) => {
      if (msg.type === 'director_update' && msg.message) {
        try {
          const data = JSON.parse(msg.message);
          setStatus(data);
          if (data.last_decision) {
            setLastDecision(data.last_decision);
          }
        } catch { /* ignore */ }
      }
    });
    return () => { unsubMsg(); };
  }, []);

  const handleSetMode = async (mode: DirectorMode) => {
    setActionLoading(mode);
    try {
      await directorApi.setMode(mode);
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set mode');
    } finally {
      setActionLoading(null);
    }
  };

  const handleRequestDecision = async () => {
    try {
      const decision = await directorApi.decision();
      setLastDecision(decision);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request decision');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Director Mode</h1>
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

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">Current Mode</p>
          <p className="mt-2 font-mono text-2xl text-white">
            {loading ? '—' : MODE_LABELS[status?.mode ?? 'broadcast']}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">System State</p>
          <p className="mt-2 font-mono text-2xl text-white">{status?.state ?? '—'}</p>
        </div>
      </div>

      <section className="card">
        <h2 className="text-base font-semibold text-white">Mode Selector</h2>
        <p className="mt-1 text-sm text-slate-400">
          Select the camera director operating mode.
        </p>
        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {MODES.map((mode) => (
            <button
              key={mode}
              onClick={() => handleSetMode(mode)}
              disabled={actionLoading !== null}
              className={`flex items-center justify-between rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                status?.mode === mode
                  ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400'
                  : 'border-slate-700 bg-slate-800 text-slate-200 hover:border-slate-500'
              } disabled:opacity-50`}
            >
              {MODE_LABELS[mode]}
              {actionLoading === mode && (
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              )}
            </button>
          ))}
        </div>
      </section>

      <section className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">Latest Decision</h2>
            <p className="mt-1 text-sm text-slate-400">
              Most recent director tracking decision.
            </p>
          </div>
          <button
            onClick={handleRequestDecision}
            className="flex items-center gap-2 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-500 transition-colors"
          >
            Request Decision
          </button>
        </div>
        <div className="mt-4">
          {lastDecision ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="rounded-md bg-slate-800/50 p-3">
                  <p className="text-xs text-slate-400">Pan</p>
                  <p className="mt-1 font-mono text-lg text-white">{lastDecision.target.pan_angle.toFixed(1)}°</p>
                </div>
                <div className="rounded-md bg-slate-800/50 p-3">
                  <p className="text-xs text-slate-400">Tilt</p>
                  <p className="mt-1 font-mono text-lg text-white">{lastDecision.target.tilt_angle.toFixed(1)}°</p>
                </div>
                <div className="rounded-md bg-slate-800/50 p-3">
                  <p className="text-xs text-slate-400">Zoom</p>
                  <p className="mt-1 font-mono text-lg text-white">{lastDecision.target.zoom.toFixed(2)}x</p>
                </div>
                <div className="rounded-md bg-slate-800/50 p-3">
                  <p className="text-xs text-slate-400">Transition</p>
                  <p className="mt-1 font-mono text-lg text-white">{lastDecision.target.transition_time.toFixed(2)}s</p>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-slate-300">Confidence</span>
                </div>
                <ConfidenceBar value={lastDecision.confidence} />
              </div>

              <div>
                <p className="text-sm text-slate-300">Reasoning</p>
                <p className="mt-1 text-sm text-slate-400">{lastDecision.reasoning}</p>
              </div>

              <div className="flex items-center gap-4 text-xs text-slate-500">
                <span>Mode: <span className="text-slate-300">{MODE_LABELS[lastDecision.mode]}</span></span>
                <span>Track ID: <span className="text-slate-300">{lastDecision.tracking_track_id ?? 'N/A'}</span></span>
                <span>Time: <span className="text-slate-300">{new Date(lastDecision.timestamp * 1000).toLocaleTimeString()}</span></span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">No decision data available.</p>
          )}
        </div>
      </section>
    </div>
  );
}