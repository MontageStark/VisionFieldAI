import { useState, useEffect } from 'react';
import { outputApi } from '@/services/api';

interface VirtualCameraState {
  center_x: number;
  center_y: number;
  zoom: number;
  mode: string;
}

export default function VirtualCamera(): JSX.Element {
  const [state, setState] = useState<VirtualCameraState>({
    center_x: 0.5,
    center_y: 0.5,
    zoom: 1.5,
    mode: 'virtual',
  });
  const [settings, setSettings] = useState({
    dead_zone: 0.05,
    safe_margin: 0.1,
    smoothing: 0.3,
  });

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await outputApi.getState();
        setState(response.data);
      } catch {
        // silently ignore
      }
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Virtual Camera</h1>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {/* Target Position */}
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">Target Position</p>
          <div className="mt-4 space-y-4">
            <div>
              <p className="text-sm text-slate-400">Center X</p>
              <p className="font-mono text-2xl text-white">{state.center_x.toFixed(3)}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">Center Y</p>
              <p className="font-mono text-2xl text-white">{state.center_y.toFixed(3)}</p>
            </div>
            <div>
              <p className="text-sm text-slate-400">Zoom</p>
              <p className="font-mono text-2xl text-white">{state.zoom.toFixed(2)}x</p>
            </div>
          </div>
        </div>

        {/* Frame View */}
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">Frame View</p>
          <div className="relative mt-4 aspect-video w-full overflow-hidden rounded-lg border border-slate-700 bg-slate-950">
            {/* Crosshair at target position */}
            <div
              className="absolute left-1/2 top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-brand-400 transition-all duration-300"
              style={{
                left: `${state.center_x * 100}%`,
                top: `${state.center_y * 100}%`,
              }}
            >
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="h-1 w-1 rounded-full bg-brand-400" />
              </div>
            </div>
            {/* Zoom indicator */}
            <div className="absolute bottom-2 right-2 rounded bg-slate-700/80 px-2 py-1 font-mono text-xs text-white">
              {state.zoom.toFixed(1)}x
            </div>
            {/* Grid lines */}
            <div className="pointer-events-none absolute inset-0">
              <div className="absolute bottom-0 left-1/3 top-0 w-px bg-slate-700/30" />
              <div className="absolute bottom-0 left-2/3 top-0 w-px bg-slate-700/30" />
              <div className="absolute left-0 right-0 top-1/3 h-px bg-slate-700/30" />
              <div className="absolute left-0 right-0 top-2/3 h-px bg-slate-700/30" />
            </div>
          </div>
        </div>

        {/* Settings */}
        <div className="card">
          <p className="text-xs uppercase tracking-wide text-slate-400">Settings</p>
          <div className="mt-4 space-y-5">
            <label className="block">
              <div className="mb-1 flex justify-between">
                <span className="text-sm text-slate-300">Dead Zone</span>
                <span className="font-mono text-xs text-slate-400">{settings.dead_zone.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="0.2"
                step="0.01"
                value={settings.dead_zone}
                onChange={(e) => setSettings((s) => ({ ...s, dead_zone: parseFloat(e.target.value) }))}
                className="w-full accent-brand-500"
              />
            </label>
            <label className="block">
              <div className="mb-1 flex justify-between">
                <span className="text-sm text-slate-300">Safe Margin</span>
                <span className="font-mono text-xs text-slate-400">{settings.safe_margin.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="0.3"
                step="0.01"
                value={settings.safe_margin}
                onChange={(e) => setSettings((s) => ({ ...s, safe_margin: parseFloat(e.target.value) }))}
                className="w-full accent-brand-500"
              />
            </label>
            <label className="block">
              <div className="mb-1 flex justify-between">
                <span className="text-sm text-slate-300">Smoothing</span>
                <span className="font-mono text-xs text-slate-400">{settings.smoothing.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={settings.smoothing}
                onChange={(e) => setSettings((s) => ({ ...s, smoothing: parseFloat(e.target.value) }))}
                className="w-full accent-brand-500"
              />
            </label>
          </div>
          <div className="mt-6 border-t border-slate-700 pt-4">
            <p className="text-xs text-slate-400">
              Mode: <span className="text-white">{state.mode}</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
