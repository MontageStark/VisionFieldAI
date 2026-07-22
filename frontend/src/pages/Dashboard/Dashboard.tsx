import { useState, useRef, useEffect, useMemo } from 'react';
import { Activity, Camera as CameraIcon, Cpu, Users, Zap } from 'lucide-react';
import { useApiPolling } from '@/hooks/useApiPolling';
import { cameraApi, directorApi } from '@/services/api';

export function Dashboard(): JSX.Element {
  const { data: cameraStatus } = useApiPolling(
    () => cameraApi.status(),
    3000,
  );
  const { data: directorStatus } = useApiPolling(
    () => directorApi.status(),
    5000,
  );

  const imgRef = useRef<HTMLImageElement>(null);
  const [streamError, setStreamError] = useState(false);

  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;
    const onError = () => setStreamError(true);
    const onLoad = () => setStreamError(false);
    img.addEventListener('error', onError);
    img.addEventListener('load', onLoad);
    return () => {
      img.removeEventListener('error', onError);
      img.removeEventListener('load', onLoad);
    };
  }, []);

  const isRunning = cameraStatus?.running ?? false;

  const defaultStats = useMemo(() => [
    { label: 'FPS', value: '--', icon: <Activity size={18} />, color: 'text-accent-success' },
    { label: 'Latency', value: '--', icon: <Zap size={18} />, color: 'text-primary-400' },
    { label: 'Players Detected', value: '--', icon: <Users size={18} />, color: 'text-accent-info' },
    { label: 'GPU Usage', value: '--', icon: <Cpu size={18} />, color: 'text-accent-warning' },
  ], []);

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Dashboard</h2>
        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            isRunning
              ? 'bg-accent-success/10 text-accent-success'
              : 'bg-dark-border text-slate-300'
          }`}
        >
          {isRunning ? 'LIVE' : 'OFFLINE'}
        </span>
      </div>

      <div className="flex flex-1 gap-4">
        <div className="flex-1 rounded-xl border border-dark-border bg-dark-card overflow-hidden">
          <div data-testid="live-camera-feed" className="relative h-full min-h-[300px] bg-dark-surface">
            {isRunning && !streamError ? (
              <img
                ref={imgRef}
                src="/api/camera/stream"
                alt={streamError ? 'Camera stream unavailable' : 'Live camera feed'}
                className="h-full w-full object-contain"
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <div className="mb-2 flex h-16 w-16 items-center justify-center rounded-full bg-dark-border mx-auto">
                    <CameraIcon size={24} className="text-primary-400" />
                  </div>
                  <p className="text-sm text-slate-300">Live Camera Feed</p>
                  <p className="text-xs text-slate-400">
                    {streamError ? 'Stream unavailable' : 'No signal'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="w-80 space-y-4">
          <div className="rounded-xl border border-dark-border bg-dark-card p-4">
            <h3 className="mb-1 text-sm font-semibold text-white">AI Director</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-300">Mode</span>
                <span className="text-xs font-medium text-white capitalize">
                  {directorStatus?.mode ?? 'broadcast'}
                </span>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-dark-border bg-dark-card p-4">
            <h3 className="mb-3 text-sm font-semibold text-white">System</h3>
            <div className="grid grid-cols-2 gap-2">
              {defaultStats.map((s) => (
                <div key={s.label} className="rounded-lg bg-dark-surface p-2">
                  <div className="flex items-center gap-1.5">
                    <span className={s.color}>{s.icon}</span>
                    <span className="text-[10px] text-slate-300">{s.label}</span>
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
