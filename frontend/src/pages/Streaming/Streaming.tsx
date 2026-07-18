import { Radio, Play, Square, RefreshCw } from 'lucide-react';

const destinations = [
  { name: 'RTSP', status: 'Connected', statusColor: 'text-accent-success' },
  { name: 'OBS', status: 'Connected', statusColor: 'text-accent-success' },
  { name: 'YouTube', status: 'Connected', statusColor: 'text-accent-success' },
];

const metrics = [
  { label: 'Dropped Frames', value: '0' },
  { label: 'Bitrate', value: '4.5 Mbps' },
  { label: 'Latency', value: '120ms' },
];

export function Streaming(): JSX.Element {
  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-bold text-white">Streaming</h2>

      <div className="grid grid-cols-3 gap-4">
        {destinations.map((dest) => (
          <div key={dest.name} className="rounded-xl border border-dark-border bg-dark-card p-4">
            <div className="flex items-center gap-3">
              <Radio size={20} className="text-primary-400" />
              <div>
                <h3 className="text-sm font-semibold text-white">{dest.name}</h3>
                <span className={`text-xs ${dest.statusColor}`}>{dest.status}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <h3 className="mb-4 text-sm font-semibold text-white">Stream Metrics</h3>
        <div className="grid grid-cols-3 gap-4">
          {metrics.map((m) => (
            <div key={m.label} className="rounded-lg bg-dark-surface p-3">
              <p className="text-xs text-slate-400">{m.label}</p>
              <p className="mt-1 text-lg font-bold text-white">{m.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="flex items-center gap-2 rounded-lg bg-accent-success/10 px-4 py-2 text-sm font-medium text-accent-success hover:bg-accent-success/20 transition-colors">
          <Play size={16} />
          Go Live
        </button>
        <button className="flex items-center gap-2 rounded-lg bg-accent-error/10 px-4 py-2 text-sm font-medium text-accent-error hover:bg-accent-error/20 transition-colors">
          <Square size={16} />
          Stop
        </button>
        <button className="flex items-center gap-2 rounded-lg bg-dark-card px-4 py-2 text-sm font-medium text-slate-400 hover:bg-dark-surface transition-colors">
          <RefreshCw size={16} />
          Reconnect
        </button>
      </div>
    </div>
  );
}

export default Streaming;
