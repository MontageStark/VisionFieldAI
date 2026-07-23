import { useState } from 'react';
import { Clapperboard, Brain, Crosshair, Eye } from 'lucide-react';
import { useApiPolling } from '@/hooks/useApiPolling';
import { aiApi } from '@/services/api';

const modes = [
  { id: 'broadcast', label: 'Broadcast', description: 'Standard broadcast camera behavior' },
  { id: 'aggressive', label: 'Aggressive', description: 'Fast, tight tracking' },
  { id: 'wide', label: 'Wide', description: 'Wide-angle overview' },
  { id: 'training', label: 'Training', description: 'Training session mode' },
  { id: 'manual_assist', label: 'Manual Assist', description: 'Human-assisted control' },
];

export function Director(): JSX.Element {
  const [activeMode, setActiveMode] = useState('broadcast');
  const { data: aiStatus } = useApiPolling(() => aiApi.status(), 2000);
  const { data: detections } = useApiPolling(() => aiApi.detections(), 2000);

  const tracking = aiStatus?.tracking ?? {};
  const decision = aiStatus?.decision ?? {};
  const detectionList = detections?.detections ?? [];

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-bold text-white">AI Director</h2>

      {/* Current Decision */}
      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <h3 className="mb-4 text-sm font-semibold text-white">Current Decision</h3>
        {decision.reasoning ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3 rounded-lg bg-dark-surface p-4">
              <Clapperboard size={20} className="text-primary-400" />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-white">{decision.shot_type}</span>
                  <span className="text-xs text-slate-400">zoom {decision.zoom}x</span>
                  <span className="text-xs text-primary-400">{(decision.confidence * 100).toFixed(0)}%</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">{decision.reasoning}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-lg bg-dark-surface p-3">
                <span className="text-slate-400">Target Pan</span>
                <p className="text-white font-medium">{decision.target_pan}°</p>
              </div>
              <div className="rounded-lg bg-dark-surface p-3">
                <span className="text-slate-400">Target Tilt</span>
                <p className="text-white font-medium">{decision.target_tilt}°</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3 rounded-lg bg-dark-surface p-4">
            <Clapperboard size={20} className="text-slate-600" />
            <div>
              <p className="text-sm text-slate-400">Waiting for AI pipeline...</p>
              <p className="text-xs text-slate-500">Start streaming to see real-time decisions</p>
            </div>
          </div>
        )}
      </div>

      {/* Tracking Info */}
      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <h3 className="mb-4 text-sm font-semibold text-white">Tracking</h3>
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg bg-dark-surface p-3 text-center">
            <Eye size={18} className="mx-auto mb-1 text-primary-400" />
            <p className="text-lg font-bold text-white">{tracking.fps ?? 0}</p>
            <p className="text-xs text-slate-400">FPS</p>
          </div>
          <div className="rounded-lg bg-dark-surface p-3 text-center">
            <Crosshair size={18} className="mx-auto mb-1 text-accent-info" />
            <p className="text-lg font-bold text-white">{tracking.player_count ?? 0}</p>
            <p className="text-xs text-slate-400">Motions</p>
          </div>
          <div className="rounded-lg bg-dark-surface p-3 text-center">
            <Brain size={18} className="mx-auto mb-1 text-accent-warning" />
            <p className="text-lg font-bold text-white">{tracking.frame_count ?? 0}</p>
            <p className="text-xs text-slate-400">Frames</p>
          </div>
        </div>
      </div>

      {/* Recent Detections */}
      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <h3 className="mb-4 text-sm font-semibold text-white">Recent Detections</h3>
        {detectionList.length > 0 ? (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {detectionList.slice(0, 10).map((d: any, i: number) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-dark-surface px-3 py-2">
                <span className="text-xs text-white">{d.label}</span>
                <span className="text-xs text-slate-400">
                  {(d.confidence * 100).toFixed(0)}% @ ({(d.x * 100).toFixed(0)}%, {(d.y * 100).toFixed(0)}%)
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500">No detections yet</p>
        )}
      </div>

      {/* Director Mode */}
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
                  : 'bg-dark-surface border border-transparent text-slate-300 hover:bg-dark-card'
              }`}
            >
              <p className="text-sm font-medium">{mode.label}</p>
              <p className="text-xs text-slate-400">{mode.description}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Director;
