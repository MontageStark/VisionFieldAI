import { Play, Square, Camera, CircleDot, Settings } from 'lucide-react';

export function FloatingControls(): JSX.Element {
  return (
    <div data-testid="floating-controls" className="flex items-center gap-2">
      <button
        data-testid="btn-start"
        className="flex items-center gap-2 rounded-lg bg-accent-success/10 px-4 py-2 text-sm font-medium text-accent-success hover:bg-accent-success/20 transition-colors"
      >
        <Play size={16} />
        Start
      </button>
      <button
        data-testid="btn-stop"
        className="flex items-center gap-2 rounded-lg bg-accent-error/10 px-4 py-2 text-sm font-medium text-accent-error hover:bg-accent-error/20 transition-colors"
      >
        <Square size={16} />
        Stop
      </button>
      <button
        data-testid="btn-snapshot"
        className="flex items-center gap-2 rounded-lg bg-primary-500/10 px-4 py-2 text-sm font-medium text-primary-400 hover:bg-primary-500/20 transition-colors"
      >
        <Camera size={16} />
        Snapshot
      </button>
      <button
        data-testid="btn-record"
        className="flex items-center gap-2 rounded-lg bg-accent-error/10 px-4 py-2 text-sm font-medium text-accent-error hover:bg-accent-error/20 transition-colors"
      >
        <CircleDot size={16} />
        Record
      </button>
      <button
        data-testid="floating-settings"
        className="rounded-lg p-2 text-slate-400 hover:bg-dark-card hover:text-white transition-colors"
      >
        <Settings size={16} />
      </button>
    </div>
  );
}

export default FloatingControls;
