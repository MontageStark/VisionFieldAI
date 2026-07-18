import { useState } from 'react';

const mockLogs = [
  { id: '1', level: 'info', component: 'System', message: 'Application started', timestamp: '14:23:01' },
  { id: '2', level: 'info', component: 'Camera', message: 'Camera connected - 720p@15fps', timestamp: '14:23:02' },
  { id: '3', level: 'info', component: 'Director', message: 'Director mode set to broadcast', timestamp: '14:23:03' },
  { id: '4', level: 'warning', component: 'GPU', message: 'GPU usage above 80%', timestamp: '14:23:05' },
  { id: '5', level: 'error', component: 'Streaming', message: 'RTSP connection timeout', timestamp: '14:23:06' },
  { id: '6', level: 'info', component: 'Tracking', message: '11 players detected', timestamp: '14:23:07' },
];

function levelColor(level: string) {
  switch (level) {
    case 'error': return 'text-accent-error';
    case 'warning': return 'text-accent-warning';
    default: return 'text-slate-300';
  }
}

export function Logs(): JSX.Element {
  const [levelFilter, setLevelFilter] = useState('All');
  const [search, setSearch] = useState('');

  const filteredLogs = mockLogs.filter((log) => {
    if (levelFilter !== 'All' && log.level !== levelFilter.toLowerCase()) return false;
    if (search && !log.message.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-4 p-6">
      <h2 className="text-xl font-bold text-white">Logs</h2>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Level</span>
          {['All', 'Error', 'Warning', 'Info'].map((level) => (
            <button
              key={level}
              onClick={() => setLevelFilter(level)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                levelFilter === level
                  ? 'bg-primary-500/20 text-primary-400'
                  : 'text-slate-400 hover:bg-dark-card'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Component</span>
          <select className="rounded-lg border border-dark-border bg-dark-card px-3 py-1.5 text-xs text-slate-200">
            <option>All Components</option>
          </select>
        </div>
        <input
          type="text"
          placeholder="Search logs..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="rounded-lg border border-dark-border bg-dark-card px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        />
      </div>

      <div data-testid="log-viewer" className="rounded-xl border border-dark-border bg-dark-surface overflow-hidden">
        <div className="space-y-0">
          {filteredLogs.map((log) => (
            <div
              key={log.id}
              className="flex items-start gap-4 border-b border-dark-border/50 px-4 py-2.5 font-mono text-xs last:border-0"
            >
              <span className="text-slate-500 shrink-0">{log.timestamp}</span>
              <span className={`shrink-0 uppercase font-bold ${levelColor(log.level)}`}>
                {log.level}
              </span>
              <span className="text-primary-400 shrink-0">{log.component}</span>
              <span className="text-slate-300">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Logs;
