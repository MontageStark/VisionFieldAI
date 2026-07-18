import { Play, Save, Download } from 'lucide-react';

const events = [
  { time: '00:12:34', type: 'Goal', description: 'Player #7 scores from center' },
  { time: '00:28:15', type: 'Corner', description: 'Corner kick by team A' },
  { time: '00:45:02', type: 'Throw', description: 'Throw-in at midfield' },
];

export function Replay(): JSX.Element {
  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-bold text-white">Match Replay</h2>

      <div data-testid="replay-timeline" className="rounded-xl border border-dark-border bg-dark-card p-4">
        <div className="mb-4 flex items-center justify-between">
          <span className="text-sm font-semibold text-white">Match Timeline</span>
          <span className="text-xs text-slate-400">45:00 / 90:00</span>
        </div>

        <div className="relative h-12 w-full rounded-lg bg-dark-surface">
          <div className="absolute left-0 top-0 h-full w-1/2 rounded-lg bg-primary-500/20" />
          <div className="absolute left-1/2 top-0 h-full w-0.5 bg-primary-500" />

          {events.map((_evt, i) => (
            <div
              key={i}
              className="absolute top-1/2 -translate-y-1/2"
              style={{ left: `${(i + 1) * 25}%` }}
            >
              <div className="h-3 w-3 rounded-full bg-accent-success border-2 border-dark-card" />
            </div>
          ))}
        </div>

        <div className="mt-4 space-y-2">
          {events.map((event, i) => (
            <div key={i} className="flex items-center gap-3 rounded-lg bg-dark-surface px-3 py-2">
              <span className="text-xs font-mono text-slate-500">{event.time}</span>
              <span className="rounded-full bg-primary-500/10 px-2 py-0.5 text-xs font-medium text-primary-400">
                {event.type}
              </span>
              <span className="text-xs text-slate-300">{event.description}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="flex items-center gap-2 rounded-lg bg-accent-success/10 px-4 py-2 text-sm font-medium text-accent-success hover:bg-accent-success/20 transition-colors">
          <Play size={16} />
          Replay
        </button>
        <button className="flex items-center gap-2 rounded-lg bg-primary-500/10 px-4 py-2 text-sm font-medium text-primary-400 hover:bg-primary-500/20 transition-colors">
          <Save size={16} />
          Save Clip
        </button>
        <button className="flex items-center gap-2 rounded-lg bg-dark-card px-4 py-2 text-sm font-medium text-slate-400 hover:bg-dark-surface transition-colors">
          <Download size={16} />
          Export
        </button>
      </div>
    </div>
  );
}

export default Replay;
