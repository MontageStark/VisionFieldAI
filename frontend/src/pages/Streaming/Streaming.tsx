import { useState, useEffect, useRef, useCallback } from 'react';
import { Radio, Play, Square, RefreshCw, Wifi, WifiOff, Brain } from 'lucide-react';
import { useApiPolling } from '@/hooks/useApiPolling';
import { aiApi } from '@/services/api';

const API_BASE = window.location.port === '5173'
  ? 'http://localhost:8001'
  : '';

type StreamState = 'idle' | 'connecting' | 'live' | 'reconnecting' | 'offline';

export function Streaming(): JSX.Element {
  const [isLive, setIsLive] = useState(false);
  const [phoneIp, setPhoneIp] = useState('192.168.0.187');
  const [streamKey, setStreamKey] = useState(0);
  const [state, setState] = useState<StreamState>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [fps, setFps] = useState(0);
  const imgRef = useRef<HTMLImageElement>(null);
  const frameCountRef = useRef(0);
  const lastFpsTime = useRef(Date.now());

  const { data: aiStatus } = useApiPolling(() => aiApi.status(), 2000);
  const decision = aiStatus?.decision ?? {};

  const streamUrl = `${API_BASE}/api/stream/proxy?phone_ip=${phoneIp}&port=8080&_t=${streamKey}`;

  const startLive = useCallback(() => {
    setIsLive(true);
    setState('connecting');
    setErrorMsg('');
    setStreamKey(k => k + 1);
    frameCountRef.current = 0;
    lastFpsTime.current = Date.now();
  }, []);

  const stopLive = useCallback(() => {
    setIsLive(false);
    setState('idle');
    setErrorMsg('');
    setFps(0);
  }, []);

  const reconnect = useCallback(() => {
    setState('reconnecting');
    setErrorMsg('');
    setStreamKey(k => k + 1);
    frameCountRef.current = 0;
    lastFpsTime.current = Date.now();
  }, []);

  useEffect(() => {
    if (!isLive) return;
    const img = imgRef.current;
    if (!img) return;

    const onLoad = () => {
      setState('live');
      setErrorMsg('');
      frameCountRef.current++;
      const now = Date.now();
      const elapsed = (now - lastFpsTime.current) / 1000;
      if (elapsed >= 1) {
        setFps(Math.round(frameCountRef.current / elapsed));
        frameCountRef.current = 0;
        lastFpsTime.current = now;
      }
    };

    const onError = () => {
      if (state === 'live' || state === 'reconnecting') {
        setState('reconnecting');
        setErrorMsg('Connection lost. Reconnecting...');
        setTimeout(() => setStreamKey(k => k + 1), 2000);
      } else {
        setState('offline');
        setErrorMsg('Cannot reach phone camera. Check WiFi and IP address.');
        setIsLive(false);
      }
    };

    img.addEventListener('load', onLoad);
    img.addEventListener('error', onError);
    return () => {
      img.removeEventListener('load', onLoad);
      img.removeEventListener('error', onError);
    };
  }, [isLive, streamKey]);

  const stateConfig: Record<StreamState, { label: string; color: string; icon: React.ReactNode }> = {
    idle: { label: 'Offline', color: 'text-slate-500', icon: <Radio size={48} className="text-slate-600" /> },
    connecting: { label: 'Connecting...', color: 'text-yellow-400', icon: <RefreshCw size={32} className="animate-spin text-yellow-400" /> },
    live: { label: 'Live', color: 'text-green-400', icon: <Radio size={32} className="text-green-400" /> },
    reconnecting: { label: 'Reconnecting...', color: 'text-orange-400', icon: <RefreshCw size={32} className="animate-spin text-orange-400" /> },
    offline: { label: 'Offline', color: 'text-red-400', icon: <WifiOff size={32} className="text-red-400" /> },
  };

  const cfg = stateConfig[state];

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Streaming</h2>
        {state === 'live' && fps > 0 && (
          <div className="flex items-center gap-2 text-sm text-green-400">
            <div className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
            {fps} FPS
          </div>
        )}
      </div>

      {/* Phone IP config */}
      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <div className="flex items-center gap-3">
          <Wifi size={20} className="text-primary-400" />
          <div className="flex-1">
            <label className="text-xs text-slate-400">Phone Stream IP</label>
            <input
              type="text"
              value={phoneIp}
              onChange={(e) => setPhoneIp(e.target.value)}
              className="mt-1 w-full rounded-lg bg-dark-surface px-3 py-2 text-sm text-white border border-dark-border focus:border-primary-400 focus:outline-none"
              placeholder="192.168.x.x"
              disabled={isLive}
            />
          </div>
        </div>
      </div>

      {/* Live preview */}
      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white">Live Preview</h3>
          <span className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
        </div>
        <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-black">
          {isLive && (
            <>
              <img
                ref={imgRef}
                key={streamKey}
                src={streamUrl}
                alt="Live camera feed"
                className="h-full w-full object-contain"
              />
              {/* Virtual broadcast camera overlay */}
              {(decision.crop_w ?? 1) < 1 && (
                <>
                  <div
                    className="absolute inset-0 bg-black/40 transition-all duration-300 pointer-events-none"
                    style={{
                      clipPath: `polygon(
                        0% 0%, 100% 0%, 100% 100%, 0% 100%,
                        0% ${((decision.crop_y ?? 0.5) - (decision.crop_h ?? 1) / 2) * 100}%,
                        ${((decision.crop_x ?? 0.5) - (decision.crop_w ?? 1) / 2) * 100}% ${((decision.crop_y ?? 0.5) - (decision.crop_h ?? 1) / 2) * 100}%,
                        ${((decision.crop_x ?? 0.5) - (decision.crop_w ?? 1) / 2) * 100}% ${((decision.crop_y ?? 0.5) + (decision.crop_h ?? 1) / 2) * 100}%,
                        ${((decision.crop_x ?? 0.5) + (decision.crop_w ?? 1) / 2) * 100}% ${((decision.crop_y ?? 0.5) + (decision.crop_h ?? 1) / 2) * 100}%,
                        ${((decision.crop_x ?? 0.5) + (decision.crop_w ?? 1) / 2) * 100}% ${((decision.crop_y ?? 0.5) - (decision.crop_h ?? 1) / 2) * 100}%
                      )`,
                    }}
                  />
                  <div
                    className="absolute border-[3px] border-green-400 rounded-sm pointer-events-none transition-all duration-300 ease-out shadow-[0_0_12px_rgba(74,222,128,0.3)]"
                    style={{
                      left: `${((decision.crop_x ?? 0.5) - (decision.crop_w ?? 1) / 2) * 100}%`,
                      top: `${((decision.crop_y ?? 0.5) - (decision.crop_h ?? 1) / 2) * 100}%`,
                      width: `${(decision.crop_w ?? 1) * 100}%`,
                      height: `${(decision.crop_h ?? 1) * 100}%`,
                    }}
                  />
                </>
              )}
              {/* Shot type badge */}
              {decision.shot_type && (
                <div className="absolute top-3 left-3 rounded-lg bg-black/70 px-3 py-1.5">
                  <div className="flex items-center gap-2">
                    <Brain size={14} className="text-primary-400" />
                    <span className="text-xs font-medium text-primary-300">{decision.shot_type}</span>
                    <span className="text-xs text-slate-400">{decision.zoom}x</span>
                  </div>
                </div>
              )}
            </>
          )}
          {!isLive && (
            <div className="flex h-full items-center justify-center text-slate-500">
              <div className="text-center">
                {cfg.icon}
                <p className="text-sm mt-3">Tap Go Live to start the camera feed</p>
              </div>
            </div>
          )}
          {(state === 'connecting' || state === 'reconnecting') && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60">
              <div className="text-center">
                {cfg.icon}
                <p className="text-sm text-slate-300 mt-2">{cfg.label}</p>
              </div>
            </div>
          )}
          {errorMsg && state !== 'idle' && (
            <div className="absolute bottom-0 left-0 right-0 bg-red-900/80 p-3 text-center">
              <p className="text-sm text-red-200">{errorMsg}</p>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {!isLive ? (
          <button
            onClick={startLive}
            className="flex items-center gap-2 rounded-lg bg-accent-success/10 px-4 py-2 text-sm font-medium text-accent-success hover:bg-accent-success/20 transition-colors"
          >
            <Play size={16} />
            Go Live
          </button>
        ) : (
          <button
            onClick={stopLive}
            className="flex items-center gap-2 rounded-lg bg-accent-error/10 px-4 py-2 text-sm font-medium text-accent-error hover:bg-accent-error/20 transition-colors"
          >
            <Square size={16} />
            Stop
          </button>
        )}
        {isLive && state !== 'live' && (
          <button
            onClick={reconnect}
            className="flex items-center gap-2 rounded-lg bg-dark-card px-4 py-2 text-sm font-medium text-slate-300 hover:bg-dark-surface transition-colors"
          >
            <RefreshCw size={16} />
            Reconnect
          </button>
        )}
      </div>
    </div>
  );
}

export default Streaming;
