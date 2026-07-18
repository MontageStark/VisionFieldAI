import { useLocation } from 'react-router-dom';
import { useSystemStore } from '@/stores/systemStore';

const routeTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/camera': 'Camera',
  '/director': 'AI Director',
  '/streaming': 'Streaming',
  '/servo': 'Hardware',
  '/analytics': 'Analytics',
  '/replay': 'Replay',
  '/recording': 'Recording',
  '/matches': 'Matches',
  '/settings': 'Settings',
  '/logs': 'Logs',
};

function pageTitle(pathname: string): string {
  if (routeTitles[pathname]) return routeTitles[pathname];
  for (const key of Object.keys(routeTitles)) {
    if (key !== '/' && pathname.startsWith(key)) return routeTitles[key];
  }
  return 'FieldVision AI';
}

function stateColor(state: string): string {
  switch (state) {
    case 'STREAMING': return 'bg-accent-success';
    case 'TRACKING': return 'bg-primary-500';
    case 'IDLE': return 'bg-accent-warning';
    default: return 'bg-slate-500';
  }
}

function wsColor(s: string): string {
  switch (s) {
    case 'open': return 'bg-accent-success';
    case 'connecting': return 'bg-accent-warning';
    case 'error': return 'bg-accent-error';
    default: return 'bg-slate-500';
  }
}

export function Header(): JSX.Element {
  const location = useLocation();
  const systemState = useSystemStore((s) => s.systemState);
  const apiConnected = useSystemStore((s) => s.apiConnected);
  const wsStatus = useSystemStore((s) => s.wsStatus);

  const isLive = systemState === 'STREAMING' || systemState === 'TRACKING';

  return (
    <header className="flex h-16 items-center justify-between border-b border-dark-border bg-dark-surface px-6" data-testid="header">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-white">{pageTitle(location.pathname)}</h1>
        {isLive && (
          <span data-testid="live-indicator" className="flex items-center gap-1.5 rounded-full bg-accent-error/10 px-2.5 py-0.5 text-xs font-medium text-accent-error">
            <span className="h-1.5 w-1.5 rounded-full bg-accent-error animate-pulse-live" />
            LIVE
          </span>
        )}
      </div>
      <div className="flex items-center gap-4 text-xs">
        <span
          data-testid="system-state"
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 font-medium ${stateColor(systemState)} bg-opacity-10 text-white`}
        >
          {systemState}
        </span>
        <div className="flex items-center gap-2">
          <span
            data-testid="api-status"
            className={`inline-block h-2.5 w-2.5 rounded-full ${apiConnected ? 'bg-accent-success' : 'bg-accent-error'}`}
          />
          <span className="text-slate-400">API</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            data-testid="ws-status"
            className={`inline-block h-2.5 w-2.5 rounded-full ${wsColor(wsStatus)}`}
          />
          <span className="text-slate-400">WS</span>
        </div>
      </div>
    </header>
  );
}

export default Header;
