import { useState, useEffect } from 'react';
import { Home, AlertTriangle } from 'lucide-react';
import { servoApi, outputApi } from '@/services/api';
import type { ServoStatus } from '@/types/api';

export function Servo(): JSX.Element {
  const [panAngle, setPanAngle] = useState(90);
  const [tiltAngle, setTiltAngle] = useState(90);

  useEffect(() => {
    servoApi.status().then((data: ServoStatus) => {
      setPanAngle(data.pan);
      setTiltAngle(data.tilt);
    }).catch(() => {});
    outputApi.getMode().catch(() => {});
  }, []);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Hardware</h2>
        <span className="rounded-full bg-accent-success/10 px-3 py-1 text-xs font-medium text-accent-success">
          Connected
        </span>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-xl border border-dark-border bg-dark-card p-4">
          <h3 className="mb-4 text-sm font-semibold text-white">Pan / Tilt</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg bg-dark-surface p-3 text-center">
              <p className="text-xs text-slate-400">Pan</p>
              <p className="text-2xl font-bold text-white">{panAngle}°</p>
            </div>
            <div className="rounded-lg bg-dark-surface p-3 text-center">
              <p className="text-xs text-slate-400">Tilt</p>
              <p className="text-2xl font-bold text-white">{tiltAngle.toFixed(1)}°</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-dark-border bg-dark-card p-4">
          <h3 className="mb-4 text-sm font-semibold text-white">Calibration</h3>
          <div className="space-y-3">
            <button className="w-full rounded-lg bg-dark-surface px-4 py-2.5 text-left text-sm text-slate-300 hover:bg-dark-border transition-colors">
              Center
            </button>
            <button className="w-full rounded-lg bg-dark-surface px-4 py-2.5 text-left text-sm text-slate-300 hover:bg-dark-border transition-colors">
              Left Limit
            </button>
            <button className="w-full rounded-lg bg-dark-surface px-4 py-2.5 text-left text-sm text-slate-300 hover:bg-dark-border transition-colors">
              Right Limit
            </button>
            <button className="w-full rounded-lg bg-primary-500/10 px-4 py-2.5 text-left text-sm font-medium text-primary-400 hover:bg-primary-500/20 transition-colors">
              Save
            </button>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="flex items-center gap-2 rounded-lg bg-primary-500/10 px-4 py-2 text-sm font-medium text-primary-400 hover:bg-primary-500/20 transition-colors">
          <Home size={16} />
          Home
        </button>
        <button className="flex items-center gap-2 rounded-lg bg-accent-error/10 px-4 py-2 text-sm font-medium text-accent-error hover:bg-accent-error/20 transition-colors">
          <AlertTriangle size={16} />
          Emergency Stop
        </button>
      </div>
    </div>
  );
}

export default Servo;
