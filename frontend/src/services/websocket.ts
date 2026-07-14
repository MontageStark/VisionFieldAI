import type { WebSocketMessage } from '@/types/api';

type Listener = (msg: WebSocketMessage) => void;
type StatusListener = (status: ConnectionStatus) => void;

export type ConnectionStatus = 'idle' | 'connecting' | 'open' | 'closed' | 'error';

interface ClientOptions {
  url: string;
  reconnectIntervalMs?: number;
  maxReconnectAttempts?: number;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectIntervalMs: number;
  private maxReconnectAttempts: number;
  private attempts = 0;
  private status: ConnectionStatus = 'idle';
  private listeners = new Set<Listener>();
  private statusListeners = new Set<StatusListener>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;

  constructor(options: ClientOptions) {
    this.url = options.url;
    this.reconnectIntervalMs = options.reconnectIntervalMs ?? 3000;
    this.maxReconnectAttempts = options.maxReconnectAttempts ?? 10;
  }

  connect(): void {
    if (
      this.status === 'connecting' ||
      this.status === 'open'
    ) {
      return;
    }
    this.intentionalClose = false;
    this.setStatus('connecting');
    try {
      this.ws = new WebSocket(this.url);
    } catch (err) {
      console.error('WebSocket constructor failed', err);
      this.setStatus('error');
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.attempts = 0;
      this.setStatus('open');
      // Heartbeat
      this.send({ type: 'ping' });
    };

    this.ws.onmessage = (ev: MessageEvent<string>) => {
      try {
        const parsed = JSON.parse(ev.data) as WebSocketMessage;
        this.listeners.forEach((cb) => cb(parsed));
      } catch (err) {
        console.warn('Failed to parse WS message', err);
      }
    };

    this.ws.onerror = () => {
      this.setStatus('error');
    };

    this.ws.onclose = () => {
      this.setStatus('closed');
      this.ws = null;
      if (!this.intentionalClose) {
        this.scheduleReconnect();
      }
    };
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setStatus('closed');
  }

  send(payload: unknown): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
      return true;
    }
    return false;
  }

  subscribe(topic: string): boolean {
    return this.send({ type: 'subscribe', topic });
  }

  onMessage(cb: Listener): () => void {
    this.listeners.add(cb);
    return () => this.listeners.delete(cb);
  }

  onStatus(cb: StatusListener): () => void {
    this.statusListeners.add(cb);
    cb(this.status);
    return () => this.statusListeners.delete(cb);
  }

  getStatus(): ConnectionStatus {
    return this.status;
  }

  private scheduleReconnect(): void {
    if (this.attempts >= this.maxReconnectAttempts) {
      return;
    }
    this.attempts++;
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.reconnectIntervalMs);
  }

  private setStatus(s: ConnectionStatus): void {
    this.status = s;
    this.statusListeners.forEach((cb) => cb(s));
  }
}

// Singleton client exposed to the app.
export const wsClient = new WebSocketClient({
  url:
    (typeof window !== 'undefined'
      ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
      : 'ws://localhost:5173') + '/ws',
});
