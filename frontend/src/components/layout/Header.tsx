import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { systemApi } from '@/services/api';
import { useSystemStore } from '@/stores/systemStore';
import { wsClient } from '@/services/websocket';

const titleByPath: Record<string, string> = {
  '/': 'Dashboard',
  '/camera': 'Camera Control',
  '/servo': 'Servo Control',
  '/director': 'Director Mode',
  '/streaming': 'Streaming',
  '/replay': 'Replay Viewer',
  '/health': 'System Health',
  '/logs': 'Logs',
  '/plugins': 'Plugin Marketplace',
  '/calibration': 'Calibration Wizard',
  '/settings': 'Settings',
};

function pageTitle(pathname: string): string {
  if (titleByPath[pathname]) return titleByPath[pathname];
  // Match dynamic routes
  for (const key of Object.keys(titleByPath)) {
    if (key !== '/' && pathname.startsWith(key)) return titleByPath[key]!;
  }
  return 'FieldVision AI';
}

function statusColor(s: ReturnType<typeof useSystemStore.getState>['wsStatus']): string {
  switch (s) {
    case 'open':
      return 'bg-emerald-500';
    case 'connecting':
      return 'bg-amber-500';
    case 'error':
      return 'bg-rose-500';
    default:
      return 'bg-slate-500';
  }
}

export function Header(): JSX.Element {
  const location = useLocation();
  const systemState = useSystemStore((s) => s.systemState);
  const apiConnected = useSystemStore((s) => s.apiConnected);
  const wsStatus = useSystemStore((s) => s.wsStatus);
  const setApiConnected = useSystemStore((s) => s.setApiConnected);
  const setWsStatus = useSystemStore((s) => s.setWsStatus);
  const setSystemState = useSystemStore((s) => s.setSystemState);
  const setError = useSystemStore((s) => s.setError);

  useEffect(() => {
    let cancelled = false;
    systemApi
      .status()
      .then((data) => {
        if (cancelled) return;
        setSystemState(data.state, data.valid_transitions);
        setApiConnected(true);
      })
      .catch((err) => {
        if (cancelled) return;
        setApiConnected(false);
        setError(err?.message ?? 'API unreachable');
      });

    const unsubscribeStatus = wsClient.onStatus((s) => setWsStatus(s));
    wsClient.connect();

    return () => {
      cancelled = true;
      unsubscribeStatus();
    };
  }, [setApiConnected, setError, setSystemState, setWsStatus]);

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-800 bg-slate-950/60 px-6">
      <div>
        <h1 className="text-lg font-semibold text-white">{pageTitle(location.pathname)}</h1>
        <p className="text-xs text-slate-400">
          System state: <span className="font-mono text-slate-200">{systemState}</span>
        </p>
      </div>
      <div className="flex items-center gap-4 text-xs">
        <div className="flex items-center gap-2">
          <span
            className={`inline-block h-2.5 w-2.5 rounded-full ${apiConnected ? 'bg-emerald-500' : 'bg-rose-500'}`}
            aria-hidden="true"
          />
          <span className="text-slate-300">API</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`inline-block h-2.5 w-2.5 rounded-full ${statusColor(wsStatus)}`}
            aria-hidden="true"
          />
          <span className="text-slate-300">WS: {wsStatus}</span>
        </div>
      </div>
    </header>
  );
}

export default Header;
