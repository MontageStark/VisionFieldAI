import axios, { AxiosError, AxiosInstance } from 'axios';
import type { DirectorStatus, ServoStatus } from '@/types/api';

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

// ─── Camera ────────────────────────────────────────────────────────────
export const cameraApi = {
  status: () => client.get('/camera/status').then((r) => r.data).catch(handleError),
};

// ─── Servo ─────────────────────────────────────────────────────────────
export const servoApi = {
  status: () => client.get<ServoStatus>('/servo/status').then((r) => r.data).catch(handleError),
};

// ─── Director ──────────────────────────────────────────────────────────
export const directorApi = {
  status: () =>
    client.get<DirectorStatus>('/director/status').then((r) => r.data).catch(handleError),
};

// ─── Output ────────────────────────────────────────────────────────────
export const outputApi = {
  setMode: (mode: string) => client.post('/output/mode', { mode }).then((r) => r.data).catch(handleError),
};

export default client;
