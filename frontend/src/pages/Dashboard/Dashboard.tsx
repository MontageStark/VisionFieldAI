import { useEffect, useState } from 'react';
import { systemApi } from '@/services/api';
import { useSystemStore } from '@/stores/systemStore';
import type { HealthCheck } from '@/types/api';

export function Dashboard(): JSX.Element {
  const systemState = useSystemStore((s) => s.systemState);
  const validTransitions = useSystemStore((s) => s.validTransitions);
  const setSystemState = useSystemStore((s) => s.setSystemState);
  const apiConnected = useSystemStore((s) => s.apiConnected);
  const wsStatus = useSystemStore((s) => s.wsStatus);
  const [health, setHealth] = useState<HealthCheck | null>(null);

  useEffect(() => {
    systemApi
      .status()
      .then((data) => setSystemState(data.state, data.valid_transitions))
      .catch(() => undefined);
    systemApi
      .health()
      .then(setHealth)
      .catch(() => undefined);
  }, [setSystemState]);

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">System State</p>
          <p className="mt-2 font-mono text-2xl text-white">{systemState}</p>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">API</p>
          <p className={`mt-2 font-mono text-lg ${apiConnected ? 'text-emerald-400' : 'text-rose-400'}`}>
            {apiConnected ? 'Connected' : 'Disconnected'}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">WebSocket</p>
          <p className="mt-2 font-mono text-lg text-white">{wsStatus}</p>
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
        </p>
        <ul className="mt-3 flex flex-wrap gap-2">
          {validTransitions.length === 0 ? (
            <li className="text-sm text-slate-500">No outgoing transitions available.</li>
          ) : (
            validTransitions.map((t) => (
              <li
                key={t}
                className="rounded-md border border-slate-700 bg-slate-800 px-2.5 py-1 font-mono text-xs text-slate-200"
              >
                {t}
              </li>
            ))
          )}
        </ul>
      </section>

      <section className="card">
        <h2 className="text-base font-semibold text-white">Live Modules</h2>
        <p className="mt-1 text-sm text-slate-400">
          This dashboard will surface real-time metrics, alerts, and recent events as backend
          services come online. Use the sidebar to navigate to feature pages.
        </p>
      </section>
    </div>
  );
}

export default Dashboard;
