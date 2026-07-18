import { useState } from 'react';

const modes = [
  { id: 'broadcast', label: 'Broadcast', description: 'Standard broadcast camera behavior' },
  { id: 'aggressive', label: 'Aggressive', description: 'Fast, tight tracking' },
  { id: 'wide', label: 'Wide', description: 'Wide-angle overview' },
  { id: 'training', label: 'Training', description: 'Training session mode' },
  { id: 'manual_assist', label: 'Manual Assist', description: 'Human-assisted control' },
];

export function Director(): JSX.Element {
  const [activeMode, setActiveMode] = useState('broadcast');

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-bold text-white">AI Director</h2>

      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <h3 className="mb-4 text-sm font-semibold text-white">Current Decision</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Reasoning</span>
            <span className="text-sm text-slate-200">Ball near penalty area, zooming in</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Confidence</span>
            <span className="text-sm font-bold text-accent-success">95%</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">Zoom Level</span>
            <span className="text-sm font-bold text-primary-400">2.0x</span>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <h3 className="mb-4 text-sm font-semibold text-white">Director Mode</h3>
        <div className="space-y-2">
          {modes.map((mode) => (
            <button
              key={mode.id}
              data-active={activeMode === mode.id ? 'true' : 'false'}
              onClick={() => setActiveMode(mode.id)}
              className={`w-full rounded-lg px-4 py-3 text-left transition-colors ${
                activeMode === mode.id
                  ? 'bg-primary-500/10 border border-primary-500/30 text-primary-400'
                  : 'bg-dark-surface border border-transparent text-slate-400 hover:bg-dark-border'
              }`}
            >
              <span className="text-sm font-medium">{mode.label}</span>
              <p className="text-xs text-slate-500 mt-0.5">{mode.description}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Director;
