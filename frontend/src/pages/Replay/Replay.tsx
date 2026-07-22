import { Play, Save, Download } from 'lucide-react';

export function Replay(): JSX.Element {
  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-bold text-white">Match Replay</h2>

      <div data-testid="replay-timeline" className="rounded-xl border border-dark-border bg-dark-card p-4">
        <div className="mb-4 flex items-center justify-between">
          <span className="text-sm font-semibold text-white">Match Timeline</span>
          <span className="text-xs text-slate-300">--:-- / --:--</span>
        </div>

        <div className="relative h-12 w-full rounded-lg bg-dark-surface">
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs text-slate-400">No recording data</span>
          </div>
        </div>

        <div className="mt-4 space-y-2">
          <div className="flex items-center gap-3 rounded-lg bg-dark-surface px-3 py-4">
            <span className="text-xs text-slate-400">Start a recording to see events here</span>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button className="flex items-center gap-2 rounded-lg bg-accent-success/10 px-4 py-2 text-sm font-medium text-accent-success hover:bg-accent-success/20 transition-colors">
          <Play size={16} />
          Replay
        </button>
        <button className="flex items-center gap-2 rounded-lg bg-primary-500/10 px-4 py-2 text-sm font-medium text-primary-400 hover:bg-primary-500/20 transition-colors">
          <Save size={16} />
          Save Clip
        </button>
        <button className="flex items-center gap-2 rounded-lg bg-dark-card px-4 py-2 text-sm font-medium text-slate-300 hover:bg-dark-surface transition-colors">
          <Download size={16} />
          Export
        </button>
      </div>
    </div>
  );
}

export default Replay;
