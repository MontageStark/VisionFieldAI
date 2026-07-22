import { useState } from 'react';

export function VirtualCamera(): JSX.Element {
  const [zoom, setZoom] = useState(1.5);
  const [deadZone, setDeadZone] = useState(20);
  const [motionSpeed, setMotionSpeed] = useState(50);

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-bold text-white">Virtual Camera</h2>

      <div className="rounded-xl border border-dark-border bg-dark-card p-6">
        <div
          data-testid="virtual-camera-frame"
          className="relative mx-auto aspect-video max-w-2xl rounded-lg bg-dark-surface border-2 border-dashed border-dark-border overflow-hidden"
        >
          <div
            className="absolute border-2 border-primary-500 bg-primary-500/10 rounded-md transition-all duration-300"
            style={{
              width: `${100 / zoom}%`,
              height: `${100 / zoom}%`,
              left: `${50 - 50 / zoom}%`,
              top: `${50 - 50 / zoom}%`,
            }}
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-xs font-mono text-primary-400">Frame</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        <div className="rounded-xl border border-dark-border bg-dark-card p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-white">Zoom</span>
            <span className="text-sm font-bold text-primary-400">{zoom.toFixed(1)}x</span>
          </div>
          <input
            type="range"
            min="1"
            max="5"
            step="0.1"
            value={zoom}
            onChange={(e) => setZoom(parseFloat(e.target.value))}
            aria-label="Zoom level"
            className="w-full accent-primary-500"
          />
        </div>

        <div className="rounded-xl border border-dark-border bg-dark-card p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-white">Dead Zone</span>
            <span className="text-sm font-bold text-primary-400">{deadZone}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="50"
            value={deadZone}
            onChange={(e) => setDeadZone(parseInt(e.target.value))}
            aria-label="Dead zone size"
            className="w-full accent-primary-500"
          />
        </div>

        <div className="rounded-xl border border-dark-border bg-dark-card p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-white">Motion Speed</span>
            <span className="text-sm font-bold text-primary-400">{motionSpeed}%</span>
          </div>
          <input
            type="range"
            min="10"
            max="100"
            value={motionSpeed}
            onChange={(e) => setMotionSpeed(parseInt(e.target.value))}
            aria-label="Motion speed"
            className="w-full accent-primary-500"
          />
        </div>
      </div>
    </div>
  );
}

export default VirtualCamera;
