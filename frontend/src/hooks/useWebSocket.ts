import { useState, useEffect, useCallback, useRef } from 'react';

type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketOptions {
  url: string;
  enabled?: boolean;
  onMessage?: (data: unknown) => void;
  onStatusChange?: (status: WebSocketStatus) => void;
}

interface UseWebSocketReturn {
  data: unknown;
  status: WebSocketStatus;
  send: (data: unknown) => void;
  disconnect: () => void;
  reconnect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const { url, enabled = true, onMessage, onStatusChange } = options;
  const [data, setData] = useState<unknown>(null);
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const updateStatus = useCallback((newStatus: WebSocketStatus) => {
    setStatus(newStatus);
    onStatusChange?.(newStatus);
  }, [onStatusChange]);

  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      updateStatus('connecting');
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        updateStatus('connected');
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          setData(parsed);
          onMessage?.(parsed);
        } catch {
          setData(event.data);
          onMessage?.(event.data);
        }
      };

      ws.onclose = () => {
        updateStatus('disconnected');
        wsRef.current = null;

        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };

      ws.onerror = () => {
        updateStatus('error');
      };
    } catch {
      updateStatus('error');
    }
  }, [url, enabled, onMessage, updateStatus]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    updateStatus('disconnected');
    reconnectAttempts.current = maxReconnectAttempts;
  }, [updateStatus]);

  const send = useCallback((payload: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof payload === 'string' ? payload : JSON.stringify(payload));
    }
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttempts.current = 0;
    connect();
  }, [connect, disconnect]);

  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      disconnect();
    }

    return () => disconnect();
  }, [enabled, connect, disconnect]);

  return { data, status, send, disconnect, reconnect };
}

export default useWebSocket;
