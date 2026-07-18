import { Activity, Cpu, Users, Zap } from 'lucide-react';

const stats = [
  { label: 'FPS', value: '60', icon: <Activity size={18} />, color: 'text-accent-success' },
  { label: 'Latency', value: '12ms', icon: <Zap size={18} />, color: 'text-primary-400' },
  { label: 'Players Detected', value: '11', icon: <Users size={18} />, color: 'text-accent-info' },
  { label: 'GPU Usage', value: '45%', icon: <Cpu size={18} />, color: 'text-accent-warning' },
];

export function Dashboard(): JSX.Element {
  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Dashboard</h2>
        <span className="rounded-full bg-primary-500/10 px-3 py-1 text-xs font-medium text-primary-400">
          TRACKING
        </span>
      </div>

      <div className="flex flex-1 gap-4">
        <div className="flex-1 rounded-xl border border-dark-border bg-dark-card overflow-hidden">
          <div data-testid="live-camera-feed" className="relative h-full min-h-[300px] bg-dark-surface flex items-center justify-center">
            <div className="text-center">
              <div className="mb-2 flex h-16 w-16 items-center justify-center rounded-full bg-dark-border mx-auto">
                <Activity size={24} className="text-primary-400" />
              </div>
              <p className="text-sm text-slate-400">Live Camera Feed</p>
              <p className="text-xs text-slate-500">No signal</p>
            </div>
          </div>
        </div>

        <div className="w-80 space-y-4">
          <div className="rounded-xl border border-dark-border bg-dark-card p-4">
            <h3 className="mb-1 text-sm font-semibold text-white">AI Director</h3>
            <p className="mb-3 text-xs text-slate-400">Current Decision</p>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Mode</span>
                <span className="text-xs font-medium text-white">Broadcast</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Confidence</span>
                <span className="text-xs font-medium text-accent-success">98%</span>
              </div>
              <p className="text-xs text-slate-300 rounded-lg bg-dark-surface p-2">
                High player density moving toward goal
              </p>
            </div>
          </div>

          <div className="rounded-xl border border-dark-border bg-dark-card p-4">
            <h3 className="mb-3 text-sm font-semibold text-white">System</h3>
            <div className="grid grid-cols-2 gap-2">
              {stats.map((s) => (
                <div key={s.label} className="rounded-lg bg-dark-surface p-2">
                  <div className="flex items-center gap-1.5">
                    <span className={s.color}>{s.icon}</span>
                    <span className="text-[10px] text-slate-400">{s.label}</span>
                  </div>
                  <p className={`mt-1 text-lg font-bold ${s.color}`}>{s.value}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div data-testid="floating-controls" className="flex items-center gap-2 self-end">
        <button className="flex items-center gap-2 rounded-lg bg-accent-success/10 px-4 py-2 text-sm font-medium text-accent-success hover:bg-accent-success/20">
          Start
        </button>
        <button className="flex items-center gap-2 rounded-lg bg-accent-error/10 px-4 py-2 text-sm font-medium text-accent-error hover:bg-accent-error/20">
          Record
        </button>
      </div>
    </div>
  );
}

export default Dashboard;
