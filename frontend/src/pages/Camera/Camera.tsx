import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { RefreshCw, Camera as CameraIcon, Crosshair, RotateCcw } from 'lucide-react';
import { useApiPolling } from '@/hooks/useApiPolling';
import { cameraApi } from '@/services/api';

export function Camera(): JSX.Element {
  const { data: cameraStatus } = useApiPolling(
    () => cameraApi.status(),
    3000,
  );

  const [streamKey, setStreamKey] = useState(0);
  const imgRef = useRef<HTMLImageElement>(null);
  const [streamError, setStreamError] = useState(false);

  const handleReconnect = useCallback(() => {
    setStreamError(false);
    setStreamKey((k) => k + 1);
  }, []);

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
  }, [streamKey]);

  const isRunning = cameraStatus?.running ?? false;

  const infoCards = useMemo(() => [
    { label: 'Input Source', value: 'Phone Camera' },
    { label: 'Resolution', value: '1280x720' },
    { label: 'FPS', value: '15' },
    { label: 'Status', value: isRunning ? 'Connected' : 'Disconnected' },
  ], [isRunning]);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Camera</h2>
        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            isRunning
              ? 'bg-accent-success/10 text-accent-success'
              : 'bg-accent-error/10 text-accent-error'
          }`}
        >
          {isRunning ? 'Running' : 'Stopped'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {infoCards.map((card) => (
          <div key={card.label} className="rounded-xl border border-dark-border bg-dark-card p-4">
            <p className="text-xs text-slate-300">{card.label}</p>
            <p className="mt-1 text-lg font-bold text-white">{card.value}</p>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <div className="relative aspect-video rounded-lg bg-dark-surface overflow-hidden">
          {isRunning && !streamError ? (
            <img
              ref={imgRef}
              key={streamKey}
              src="/api/camera/stream"
              alt={streamError ? 'Camera stream unavailable' : 'Live camera feed'}
              className="h-full w-full object-contain"
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <CameraIcon size={48} className="mx-auto text-slate-500" />
                <p className="mt-3 text-sm text-slate-300">
                  {streamError ? 'Stream unavailable - is the phone streaming?' : 'Camera not connected'}
                </p>
                {isRunning && (
                  <p className="mt-1 text-xs text-slate-400">
                    Backend is running but no video source detected
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={handleReconnect}
          className="flex items-center gap-2 rounded-lg bg-primary-500/10 px-4 py-2 text-sm font-medium text-primary-400 hover:bg-primary-500/20 transition-colors"
        >
          <RefreshCw size={16} />
          Reconnect
        </button>
        <button
          aria-label="Take camera snapshot"
          className="flex items-center gap-2 rounded-lg bg-dark-card px-4 py-2 text-sm font-medium text-slate-300 hover:bg-dark-surface transition-colors"
        >
          <CameraIcon size={16} />
          Snapshot
        </button>
        <button
          aria-label="Calibrate camera"
          className="flex items-center gap-2 rounded-lg bg-dark-card px-4 py-2 text-sm font-medium text-slate-300 hover:bg-dark-surface transition-colors"
        >
          <Crosshair size={16} />
          Calibrate
        </button>
        <button
          aria-label="Reset camera settings"
          className="flex items-center gap-2 rounded-lg bg-dark-card px-4 py-2 text-sm font-medium text-slate-300 hover:bg-dark-surface transition-colors"
        >
          <RotateCcw size={16} />
          Reset
        </button>
      </div>
    </div>
  );
}

export default Camera;
