import { RefreshCw, Camera as CameraIcon, Crosshair, RotateCcw } from 'lucide-react';

const infoCards = [
  { label: 'Input Source', value: 'Phone Camera' },
  { label: 'Resolution', value: '1280×720' },
  { label: 'FPS', value: '15' },
  { label: 'Latency', value: '45ms' },
];

export function Camera(): JSX.Element {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Camera</h2>
        <span className="rounded-full bg-accent-success/10 px-3 py-1 text-xs font-medium text-accent-success">
          Running
        </span>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {infoCards.map((card) => (
          <div key={card.label} className="rounded-xl border border-dark-border bg-dark-card p-4">
            <p className="text-xs text-slate-400">{card.label}</p>
            <p className="mt-1 text-lg font-bold text-white">{card.value}</p>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <div className="h-64 rounded-lg bg-dark-surface flex items-center justify-center">
          <div className="text-center">
            <CameraIcon size={32} className="mx-auto text-slate-500" />
            <p className="mt-2 text-sm text-slate-400">Camera Feed</p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="flex items-center gap-2 rounded-lg bg-primary-500/10 px-4 py-2 text-sm font-medium text-primary-400 hover:bg-primary-500/20 transition-colors">
          <RefreshCw size={16} />
          Reconnect
        </button>
        <button className="flex items-center gap-2 rounded-lg bg-dark-card px-4 py-2 text-sm font-medium text-slate-400 hover:bg-dark-surface transition-colors">
          <CameraIcon size={16} />
          Snapshot
        </button>
        <button className="flex items-center gap-2 rounded-lg bg-dark-card px-4 py-2 text-sm font-medium text-slate-400 hover:bg-dark-surface transition-colors">
          <Crosshair size={16} />
          Calibrate
        </button>
        <button className="flex items-center gap-2 rounded-lg bg-dark-card px-4 py-2 text-sm font-medium text-slate-400 hover:bg-dark-surface transition-colors">
          <RotateCcw size={16} />
          Reset
        </button>
      </div>
    </div>
  );
}

export default Camera;
