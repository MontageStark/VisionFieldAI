import { useState, useEffect, useRef } from 'react';
import { Radio, Play, Square, RefreshCw, Wifi } from 'lucide-react';

const API_BASE = window.location.port === '5173'
  ? 'http://localhost:8001'
  : '';

export function Streaming(): JSX.Element {
  const [isLive, setIsLive] = useState(false);
  const [phoneIp, setPhoneIp] = useState('192.168.0.176');
  const [streamKey, setStreamKey] = useState(0);
  const [status, setStatus] = useState<'idle' | 'connecting' | 'live' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const imgRef = useRef<HTMLImageElement>(null);

  const startLive = () => {
    setIsLive(true);
    setStatus('live');
    setErrorMsg('');
    setStreamKey((k) => k + 1);
  };

  const stopLive = () => {
    setIsLive(false);
    setStatus('idle');
    setErrorMsg('');
  };

  // Use backend proxy to reach phone (phone WiFi blocks direct connections)
  const streamUrl = `${API_BASE}/api/stream/proxy?phone_ip=${phoneIp}&port=8080&_t=${streamKey}`;

  useEffect(() => {
    if (!isLive) return;
    const img = imgRef.current;
    if (!img) return;

    const onLoad = () => {
      setStatus('live');
      setErrorMsg('');
    };
    const onError = () => {
      setStatus('error');
      setErrorMsg('Cannot reach phone camera. Make sure Go Live is pressed on the phone.');
      setIsLive(false);
    };

    img.addEventListener('load', onLoad);
    img.addEventListener('error', onError);
    return () => {
      img.removeEventListener('load', onLoad);
      img.removeEventListener('error', onError);
    };
  }, [isLive, streamKey]);

  const destinations = [
    { name: 'RTSP', description: 'Real-Time Streaming Protocol server' },
    { name: 'OBS', description: 'Open Broadcaster Software' },
    { name: 'YouTube', description: 'YouTube Live streaming' },
  ];

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-bold text-white">Streaming</h2>

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
            />
          </div>
        </div>
      </div>

      {/* Live preview */}
      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <h3 className="mb-4 text-sm font-semibold text-white">Live Preview</h3>
        <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-black">
          {isLive ? (
            <>
              <img
                ref={imgRef}
                key={streamKey}
                src={streamUrl}
                alt="Live camera feed"
                className="h-full w-full object-contain"
              />
              {status === 'connecting' && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/60">
                  <div className="text-center">
                    <RefreshCw size={32} className="mx-auto mb-2 animate-spin text-primary-400" />
                    <p className="text-sm text-slate-300">Connecting to phone...</p>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex h-full items-center justify-center text-slate-500">
              <div className="text-center">
                <Radio size={48} className="mx-auto mb-3 text-slate-600" />
                <p className="text-sm">Tap Go Live to start the camera feed</p>
              </div>
            </div>
          )}
          {status === 'error' && errorMsg && (
            <div className="absolute bottom-0 left-0 right-0 bg-red-900/80 p-3 text-center">
              <p className="text-sm text-red-200">{errorMsg}</p>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {destinations.map((dest) => (
          <div key={dest.name} className="rounded-xl border border-dark-border bg-dark-card p-4">
            <div className="flex items-center gap-3">
              <Radio size={20} className="text-primary-400" />
              <div>
                <h3 className="text-sm font-semibold text-white">{dest.name}</h3>
                <span className="text-xs text-slate-400">{dest.description}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <h3 className="mb-4 text-sm font-semibold text-white">Stream Metrics</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-lg bg-dark-surface p-3">
            <p className="text-xs text-slate-300">Dropped Frames</p>
            <p className="mt-1 text-lg font-bold text-white">--</p>
          </div>
          <div className="rounded-lg bg-dark-surface p-3">
            <p className="text-xs text-slate-300">Bitrate</p>
            <p className="mt-1 text-lg font-bold text-white">--</p>
          </div>
          <div className="rounded-lg bg-dark-surface p-3">
            <p className="text-xs text-slate-300">Latency</p>
            <p className="mt-1 text-lg font-bold text-white">--</p>
          </div>
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
        <button
          onClick={() => { setStatus('connecting'); setStreamKey((k) => k + 1); }}
          className="flex items-center gap-2 rounded-lg bg-dark-card px-4 py-2 text-sm font-medium text-slate-300 hover:bg-dark-surface transition-colors"
        >
          <RefreshCw size={16} />
          Reconnect
        </button>
      </div>
    </div>
  );
}

export default Streaming;
