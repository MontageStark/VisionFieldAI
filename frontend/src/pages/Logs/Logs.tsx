import { useState } from 'react';
import { ScrollText } from 'lucide-react';

export function Logs(): JSX.Element {
  const [levelFilter, setLevelFilter] = useState('All');
  const [search, setSearch] = useState('');

  return (
    <div className="space-y-4 p-6">
      <h2 className="text-xl font-bold text-white">Logs</h2>

      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-300">Level</span>
          {['All', 'Error', 'Warning', 'Info'].map((level) => (
            <button
              key={level}
              onClick={() => setLevelFilter(level)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                levelFilter === level
                  ? 'bg-primary-500/20 text-primary-400'
                  : 'text-slate-300 hover:bg-dark-card'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-300">Component</span>
          <select className="rounded-lg border border-dark-border bg-dark-card px-3 py-1.5 text-xs text-slate-200">
            <option>All Components</option>
          </select>
        </div>
        <input
          type="text"
          placeholder="Search logs..."
          aria-label="Search logs"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="rounded-lg border border-dark-border bg-dark-card px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        />
      </div>

      <div data-testid="log-viewer" className="rounded-xl border border-dark-border bg-dark-surface overflow-hidden">
        <div className="flex flex-col items-center justify-center py-12">
          <ScrollText size={32} className="text-slate-500" />
          <p className="mt-3 text-sm text-slate-300">No log entries yet</p>
          <p className="text-xs text-slate-400">Start the system to see real-time logs</p>
        </div>
      </div>
    </div>
  );
}

export default Logs;
