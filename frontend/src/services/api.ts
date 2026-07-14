import axios, { AxiosError, AxiosInstance } from 'axios';
import type {
  CameraAction,
  ComponentHealth,
  DirectorDecision,
  DirectorMode,
  DirectorStatus,
  HealthCheck,
  ServoCommandRequest,
  ServoStatus,
  StreamStatus,
  SystemHealth,
  SystemState,
  SystemStateResponse,
  SystemStatusResponse,
  StateTransitionResponse,
} from '@/types/api';

const BASE_URL = '/api';

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function handleError(err: unknown): never {
  if (axios.isAxiosError(err)) {
    const ax = err as AxiosError<{ detail?: string }>;
    const detail = ax.response?.data?.detail ?? ax.message;
    throw new ApiError(String(detail), ax.response?.status);
  }
  throw new ApiError(err instanceof Error ? err.message : 'Unknown error');
}

const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 10_000,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
);

// ─── System ────────────────────────────────────────────────────────────
export const systemApi = {
  health: () => client.get<HealthCheck>('/health').then((r) => r.data).catch(handleError),
  status: () =>
    client.get<SystemStatusResponse>('/system/status').then((r) => r.data).catch(handleError),
  getState: () =>
    client.get<SystemStateResponse>('/system/state').then((r) => r.data).catch(handleError),
  setState: (state: SystemState) =>
    client
      .post<StateTransitionResponse>(`/system/state/${state}`)
      .then((r) => r.data)
      .catch(handleError),
};

// ─── Camera ────────────────────────────────────────────────────────────
export const cameraApi = {
  status: () => client.get('/camera/status').then((r) => r.data).catch(handleError),
  start: () => client.post('/camera/start').then((r) => r.data).catch(handleError),
  stop: () => client.post('/camera/stop').then((r) => r.data).catch(handleError),
};

// ─── Servo ─────────────────────────────────────────────────────────────
export const servoApi = {
  status: () => client.get<ServoStatus>('/servo/status').then((r) => r.data).catch(handleError),
  command: (req: ServoCommandRequest) =>
    client.post<ServoStatus>('/servo/command', req).then((r) => r.data).catch(handleError),
  home: () => client.post('/servo/home').then((r) => r.data).catch(handleError),
  emergency: () => client.post('/servo/emergency').then((r) => r.data).catch(handleError),
};

// ─── Director ──────────────────────────────────────────────────────────
export const directorApi = {
  status: () =>
    client.get<DirectorStatus>('/director/status').then((r) => r.data).catch(handleError),
  setMode: (mode: DirectorMode) =>
    client.post(`/director/mode/${mode}`).then((r) => r.data).catch(handleError),
  decision: () =>
    client.post<DirectorDecision>('/director/decision').then((r) => r.data).catch(handleError),
};

// ─── Stream ────────────────────────────────────────────────────────────
export const streamApi = {
  status: () => client.get<StreamStatus>('/stream/status').then((r) => r.data).catch(handleError),
  start: () => client.post('/stream/start').then((r) => r.data).catch(handleError),
  stop: () => client.post('/stream/stop').then((r) => r.data).catch(handleError),
};

// ─── Health (alias for the top-level monitoring endpoint shape) ────────
export const healthApi = {
  system: () =>
    client.get<SystemHealth>('/health/system').then((r) => r.data).catch(handleError),
  component: (name: string) =>
    client
      .get<ComponentHealth>(`/health/component/${name}`)
      .then((r) => r.data)
      .catch(handleError),
};

// Re-export for convenience
export type { CameraAction };

export default client;
