import { useEffect, useState, useCallback } from 'react';
import { systemApi, healthApi } from '@/services/api';
import { wsClient } from '@/services/websocket';
import { useSystemStore } from '@/stores/systemStore';
import type { ComponentHealth, HealthCheck, HealthStatus, SystemHealth, SystemState, WebSocketMessage } from '@/types/api';

function StatusBadge({ status }: { status: HealthStatus }) {
  const colors = {
    green: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
    yellow: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
    red: 'bg-rose-500/20 text-rose-400 border-rose-500/40',
  };
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium ${colors[status]}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${
        status === 'green' ? 'bg-emerald-400' : status === 'yellow' ? 'bg-yellow-400' : 'bg-rose-400'
      }`} />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

export function Dashboard(): JSX.Element {
  const systemState = useSystemStore((s) => s.systemState);
  const validTransitions = useSystemStore((s) => s.validTransitions);
  const setSystemState = useSystemStore((s) => s.setSystemState);
  const apiConnected = useSystemStore((s) => s.apiConnected);
  const wsStatus = useSystemStore((s) => s.wsStatus);
  const setWsStatus = useSystemStore((s) => s.setWsStatus);

  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<number>(Date.now());

  const fetchStatus = useCallback(async () => {
    try {
      const [statusData, healthData, sysHealth] = await Promise.all([
        systemApi.status(),
        systemApi.health(),
        healthApi.system(),
      ]);
      setSystemState(statusData.state, statusData.valid_transitions);
      setHealth(healthData);
      setSystemHealth(sysHealth);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
    } finally {
      setLoading(false);
      setLastRefresh(Date.now());
    }
  }, [setSystemState]);

  useEffect(() => {
    fetchStatus();
    const poll = setInterval(fetchStatus, 5000);
    return () => clearInterval(poll);
  }, [fetchStatus]);

  useEffect(() => {
    wsClient.connect();
    const unsubStatus = wsClient.onStatus((s) => {
      setWsStatus(s === 'open' ? 'open' : s === 'connecting' ? 'connecting' : 'closed');
    });
    const unsubMsg = wsClient.onMessage((msg: WebSocketMessage) => {
      if (msg.type === 'pong') return;
      if (msg.type === 'state_update' && msg.message) {
        try {
          const data = JSON.parse(msg.message);
          if (data.state) {
            setSystemState(data.state, data.valid_transitions || []);
          }
        } catch { /* ignore */ }
      }
    });
    return () => {
      unsubStatus();
      unsubMsg();
    };
  }, [setSystemState, setWsStatus]);

  const handleTransition = async (targetState: SystemState) => {
    try {
      await systemApi.setState(targetState);
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Transition failed');
    }
  };

  const timeAgo = (ts: number) => {
    const secs = Math.floor((Date.now() - ts) / 1000);
    if (secs < 5) return 'just now';
    if (secs < 60) return `${secs}s ago`;
    return `${Math.floor(secs / 60)}m ago`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
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

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">System State</p>
          <p className="mt-2 font-mono text-2xl text-white">{systemState}</p>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slex-400">API</p>
          <p className={`mt-2 font-mono text-lg ${apiConnected ? 'text-emerald-400' : 'text-rose-400'}`}>
            {apiConnected ? 'Connected' : 'Disconnected'}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">WebSocket</p>
          <p className={`mt-2 font-mono text-lg ${
            wsStatus === 'open' ? 'text-emerald-400' : wsStatus === 'connecting' ? 'text-yellow-400' : 'text-slate-400'
          }`}>
            {wsStatus}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">Backend Version</p>
          <p className="mt-2 font-mono text-lg text-slate-200">{health?.version ?? '—'}</p>
        </div>
      </section>

      <section className="card">
        <h2 className="text-base font-semibold text-white">Valid Transitions</h2>
        <p className="mt-1 text-sm text-slate-400">
          The set of state machine transitions currently allowed from <span className="font-mono">{systemState}</span>.
          Last updated: {timeAgo(lastRefresh)}
        </p>
        <ul className="mt-3 flex flex-wrap gap-2">
          {validTransitions.length === 0 ? (
            <li className="text-sm text-slate-500">No outgoing transitions available.</li>
          ) : (
            validTransitions.map((t) => (
              <button
                key={t}
                onClick={() => handleTransition(t)}
                className="rounded-md border border-slate-700 bg-slate-800 px-2.5 py-1 font-mono text-xs text-slate-200 hover:border-slate-500 hover:bg-slate-700 transition-colors"
              >
                {t}
              </button>
            ))
          )}
        </ul>
      </section>

      <section className="card">
        <h2 className="text-base font-semibold text-white">Component Health</h2>
        <p className="mt-1 text-sm text-slate-400">
          Real-time health status of all FieldVision components.
        </p>
        {loading && systemHealth === null ? (
          <div className="mt-4 flex items-center gap-2 text-sm text-slate-400">
            <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Loading components...
          </div>
        ) : systemHealth ? (
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(systemHealth.components).map(([name, comp]: [string, ComponentHealth]) => (
              <div key={name} className="flex items-start justify-between rounded-md bg-slate-800/50 p-3">
                <div>
                  <p className="font-medium text-white">{name}</p>
                  <p className="mt-0.5 text-xs text-slate-400">{comp.message || 'No issues'}</p>
                </div>
                <StatusBadge status={comp.status} />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section className="card">
        <h2 className="text-base font-semibold text-white">System History</h2>
        <p className="mt-1 text-sm text-slate-400">
          Recent state transitions.
        </p>
        <div className="mt-3 space-y-1">
          {systemHealth && (
            <p className="text-xs text-slate-500">
              Uptime: {Math.floor(systemHealth.uptime / 3600)}h {Math.floor((systemHealth.uptime % 3600) / 60)}m
            </p>
          )}
        </div>
      </section>
    </div>
  );
}

export default Dashboard;