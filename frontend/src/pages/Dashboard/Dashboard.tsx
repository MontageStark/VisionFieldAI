import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { Activity, Camera as CameraIcon, Users, Zap, Brain, Maximize, Monitor, ChevronDown } from 'lucide-react';
import { useApiPolling } from '@/hooks/useApiPolling';
import { cameraApi, aiApi } from '@/services/api';

type Quality = 'auto' | '4k' | '1080p' | '720p';

const QUALITY_MAP: Record<Quality, { label: string; width: number; height: number }> = {
  auto: { label: 'Auto', width: 0, height: 0 },
  '4k': { label: '4K', width: 3840, height: 2160 },
  '1080p': { label: '1080p', width: 1920, height: 1080 },
  '720p': { label: '720p', width: 1280, height: 720 },
};

function getNetworkQuality(): Quality {
  const conn = (navigator as any).connection;
  if (!conn) return '720p';
  const downlink = conn.downlink || 10; // Mbps
  if (downlink >= 20) return '4k';
  if (downlink >= 8) return '1080p';
  return '720p';
}

export function Dashboard(): JSX.Element {
  const { data: cameraStatus } = useApiPolling(() => cameraApi.status(), 3000);
  const { data: aiStatus } = useApiPolling(() => aiApi.status(), 2000);

  const imgRef = useRef<HTMLImageElement>(null);
  const [streamError, setStreamError] = useState(false);
  const [quality, setQuality] = useState<Quality>('auto');
  const [showQualityMenu, setShowQualityMenu] = useState(false);

  // Adaptive quality: in auto mode, detect network strength
  const activeQuality = useMemo(() => {
    if (quality !== 'auto') return quality;
    return getNetworkQuality();
  }, [quality]);

  const streamUrl = useMemo(() => {
    const q = QUALITY_MAP[activeQuality];
    const base = 'http://192.168.0.187:8080';
    if (quality === 'auto') return base;
    return `${base}?width=${q.width}&height=${q.height}`;
  }, [activeQuality, quality]);

  const enterFullscreen = useCallback(() => {
    const el = imgRef.current?.parentElement;
    if (el) {
      if (el.requestFullscreen) el.requestFullscreen();
      else if ((el as any).webkitRequestFullscreen) (el as any).webkitRequestFullscreen();
    }
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
  }, []);

  const isRunning = cameraStatus?.running ?? false;
  const aiRunning = aiStatus?.running ?? false;
  const tracking = aiStatus?.tracking ?? {};
  const decision = aiStatus?.decision ?? {};

  const stats = useMemo(() => [
    { label: 'FPS', value: tracking.fps ?? '--', icon: <Activity size={18} />, color: 'text-accent-success' },
    { label: 'Players', value: tracking.player_count ?? '--', icon: <Users size={18} />, color: 'text-accent-info' },
    { label: 'Detections', value: tracking.detection_count ?? '--', icon: <Brain size={18} />, color: 'text-primary-400' },
    { label: 'Confidence', value: decision.confidence ? `${(decision.confidence * 100).toFixed(0)}%` : '--', icon: <Zap size={18} />, color: 'text-accent-warning' },
  ], [tracking, decision]);

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Dashboard</h2>
        <div className="flex items-center gap-3">
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${
            isRunning ? 'bg-accent-success/10 text-accent-success' : 'bg-dark-border text-slate-300'
          }`}>
            {isRunning ? 'Camera Active' : 'Camera Off'}
          </span>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${
            aiRunning ? 'bg-primary-500/10 text-primary-400' : 'bg-dark-border text-slate-300'
          }`}>
            {aiRunning ? 'AI Pipeline Active' : 'AI Off'}
          </span>
        </div>
      </div>

      {/* Live preview + AI overlay */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="relative aspect-video w-full overflow-hidden rounded-xl bg-black border border-dark-border">
            <img
              ref={imgRef}
              src={streamUrl}
              alt="Live camera feed"
              className="h-full w-full transition-transform duration-200 ease-out"
              style={{
                transform: `scale(${1 / (decision.crop_w ?? 1)})`,
                transformOrigin: `${(decision.crop_x ?? 0.5) * 100}% ${(decision.crop_y ?? 0.5) * 100}%`,
              }}
              onError={() => setStreamError(true)}
              onLoad={() => setStreamError(false)}
            />
            {streamError && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/80">
                <div className="text-center">
                  <CameraIcon size={48} className="mx-auto mb-3 text-slate-600" />
                  <p className="text-sm text-slate-400">Camera feed unavailable</p>
                  <p className="text-xs text-slate-500 mt-1">Start streaming from the phone app</p>
                </div>
              </div>
            )}
            {/* Full screen button */}
            <button
              onClick={enterFullscreen}
              className="absolute top-3 right-3 rounded-lg bg-black/60 p-2 text-slate-400 hover:text-white hover:bg-black/80 transition-colors"
              title="Full screen"
            >
              <Maximize size={16} />
            </button>
          </div>

          {/* Info bar OUTSIDE the video */}
          <div className="mt-2 flex items-center justify-between rounded-lg bg-dark-card border border-dark-border px-4 py-2">
            <div className="flex items-center gap-4">
              {/* Shot type */}
              {aiRunning && decision.shot_type && (
                <div className="flex items-center gap-2">
                  <Brain size={14} className="text-green-400" />
                  <span className="text-xs font-medium text-green-300">{decision.shot_type}</span>
                  <span className="text-xs text-slate-400">{decision.zoom}x</span>
                </div>
              )}
              {/* Quality */}
              <div className="flex items-center gap-2">
                <Monitor size={14} className="text-blue-400" />
                <span className="text-xs font-medium text-blue-300">{QUALITY_MAP[activeQuality].label}</span>
              </div>
            </div>

            {/* Quality selector */}
            <div className="relative">
              <button
                onClick={() => setShowQualityMenu(!showQualityMenu)}
                className="flex items-center gap-1.5 rounded-lg bg-dark-surface px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-dark-card transition-colors"
              >
                Quality: {QUALITY_MAP[quality].label}
                <ChevronDown size={12} />
              </button>
              {showQualityMenu && (
                <div className="absolute right-0 top-full mt-1 z-10 w-32 rounded-lg bg-dark-card border border-dark-border shadow-lg">
                  {(Object.keys(QUALITY_MAP) as Quality[]).map((q) => (
                    <button
                      key={q}
                      onClick={() => { setQuality(q); setShowQualityMenu(false); }}
                      className={`w-full px-3 py-2 text-left text-xs transition-colors ${
                        quality === q
                          ? 'bg-primary-500/10 text-primary-400'
                          : 'text-slate-300 hover:bg-dark-surface'
                      }`}
                    >
                      {QUALITY_MAP[q].label}
                      {q === 'auto' && (
                        <span className="ml-1 text-slate-500">({getNetworkQuality()})</span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Stats + Director */}
        <div className="space-y-4">
          <div className="rounded-xl border border-dark-border bg-dark-card p-4">
            <h3 className="mb-3 text-sm font-semibold text-white">Pipeline Stats</h3>
            <div className="grid grid-cols-2 gap-3">
              {stats.map((s) => (
                <div key={s.label} className="rounded-lg bg-dark-surface p-3">
                  <div className="flex items-center gap-2">
                    <span className={s.color}>{s.icon}</span>
                    <span className="text-xs text-slate-400">{s.label}</span>
                  </div>
                  <p className="mt-1 text-lg font-bold text-white">{s.value}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-dark-border bg-dark-card p-4">
            <h3 className="mb-3 text-sm font-semibold text-white">Director Decision</h3>
            {decision.reasoning ? (
              <div className="space-y-2">
                <p className="text-xs text-slate-300">{decision.reasoning}</p>
                <div className="flex gap-4 text-xs text-slate-400">
                  <span>pan: {decision.target_pan}°</span>
                  <span>tilt: {decision.target_tilt}°</span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500">No decisions yet</p>
            )}
          </div>

          <div className="rounded-xl border border-dark-border bg-dark-card p-4">
            <h3 className="mb-3 text-sm font-semibold text-white">Quick Actions</h3>
            <div className="space-y-2">
              <a href="/streaming" className="block rounded-lg bg-primary-500/10 px-3 py-2 text-xs font-medium text-primary-400 hover:bg-primary-500/20 transition-colors">
                Open Streaming Page
              </a>
              <a href="/director" className="block rounded-lg bg-dark-surface px-3 py-2 text-xs font-medium text-slate-300 hover:bg-dark-card transition-colors">
                AI Director Settings
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
