import { useEffect, useState, useCallback } from 'react';
import { servoApi } from '@/services/api';
import { wsClient } from '@/services/websocket';
import type { ServoStatus, WebSocketMessage } from '@/types/api';

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

export default function Servo(): JSX.Element {
  const [status, setStatus] = useState<ServoStatus | null>(null);
  const [_loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<'command' | 'home' | 'emergency' | null>(null);

  const [pan, setPan] = useState(90);
  const [tilt, setTilt] = useState(90);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await servoApi.status();
      setStatus(data);
      if (data.pan !== undefined) setPan(Math.round(data.pan));
      if (data.tilt !== undefined) setTilt(Math.round(data.tilt));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch servo status');
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
      if (msg.type === 'servo_update' && msg.message) {
        try {
          const data = JSON.parse(msg.message);
          setStatus(data);
          if (data.pan !== undefined) setPan(Math.round(data.pan));
          if (data.tilt !== undefined) setTilt(Math.round(data.tilt));
        } catch { /* ignore */ }
      }
    });
    return () => { unsubMsg(); };
  }, []);

  const handleCommand = async () => {
    setActionLoading('command');
    try {
      await servoApi.command({ pan, tilt });
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send command');
    } finally {
      setActionLoading(null);
    }
  };

  const handleHome = async () => {
    setActionLoading('home');
    try {
      await servoApi.home();
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to home servo');
    } finally {
      setActionLoading(null);
    }
  };

  const handleEmergency = async () => {
    setActionLoading('emergency');
    try {
      await servoApi.emergency();
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Emergency stop failed');
    } finally {
      setActionLoading(null);
    }
  };

  const isEmergencyStopped = status?.is_emergency_stopped ?? false;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Servo Control</h1>
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

      {isEmergencyStopped && (
        <div className="rounded-md bg-rose-500/20 border border-rose-500/50 p-4">
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="font-semibold text-rose-400">Emergency Stop Active</p>
          </div>
          <p className="mt-1 text-sm text-rose-300">The servo has been emergency stopped. Acknowledge and home to reset.</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">Pan Angle</p>
          <p className="mt-2 font-mono text-3xl text-white">{status?.pan?.toFixed(1) ?? '—'}°</p>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">Tilt Angle</p>
          <p className="mt-2 font-mono text-3xl text-white">{status?.tilt?.toFixed(1) ?? '—'}°</p>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">State</p>
          <p className="mt-2 font-mono text-lg text-white">{status?.state ?? '—'}</p>
        </div>
      </div>

      <section className="card">
        <h2 className="text-base font-semibold text-white">Manual Control</h2>
        <p className="mt-1 text-sm text-slate-400">
          Adjust pan and tilt angles (0–180°).
        </p>
        <div className="mt-4 space-y-4">
          <div>
            <div className="flex items-center justify-between">
              <label className="text-sm text-slate-300">Pan</label>
              <span className="font-mono text-sm text-white">{pan}°</span>
            </div>
            <input
              type="range"
              min={0}
              max={180}
              value={pan}
              onChange={(e) => setPan(Number(e.target.value))}
              className="mt-2 w-full accent-emerald-500"
            />
          </div>
          <div>
            <div className="flex items-center justify-between">
              <label className="text-sm text-slate-300">Tilt</label>
              <span className="font-mono text-sm text-white">{tilt}°</span>
            </div>
            <input
              type="range"
              min={0}
              max={180}
              value={tilt}
              onChange={(e) => setTilt(Number(e.target.value))}
              className="mt-2 w-full accent-emerald-500"
            />
          </div>
          <button
            onClick={handleCommand}
            disabled={actionLoading !== null || isEmergencyStopped}
            className="flex items-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {actionLoading === 'command' ? <LoadingSpinner label="Sending..." /> : 'Apply Position'}
          </button>
        </div>
      </section>

      <section className="card">
        <h2 className="text-base font-semibold text-white">Actions</h2>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            onClick={handleHome}
            disabled={actionLoading !== null || isEmergencyStopped}
            className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {actionLoading === 'home' ? <LoadingSpinner label="Homing..." /> : 'Home Servo'}
          </button>
          <button
            onClick={handleEmergency}
            disabled={actionLoading !== null}
            className="flex items-center gap-2 rounded-md bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {actionLoading === 'emergency' ? <LoadingSpinner label="Stopping..." /> : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Emergency Stop
              </>
            )}
          </button>
        </div>
      </section>
    </div>
  );
}