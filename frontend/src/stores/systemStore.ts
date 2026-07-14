import { create } from 'zustand';
import type { HealthStatus, SystemState } from '@/types/api';

export interface SystemStoreState {
  // Connection state to backend
  apiConnected: boolean;
  wsStatus: 'idle' | 'connecting' | 'open' | 'closed' | 'error';
  lastError: string | null;

  // Live system state
  systemState: SystemState;
  validTransitions: SystemState[];
  healthStatus: HealthStatus;

  // Timestamps
  lastUpdated: number | null;

  // Actions
  setApiConnected: (ok: boolean) => void;
  setWsStatus: (s: SystemStoreState['wsStatus']) => void;
  setSystemState: (state: SystemState, validTransitions?: SystemState[]) => void;
  setHealthStatus: (s: HealthStatus) => void;
  setError: (msg: string | null) => void;
  reset: () => void;
}

export const useSystemStore = create<SystemStoreState>((set) => ({
  apiConnected: false,
  wsStatus: 'idle',
  lastError: null,

  systemState: 'BOOTING',
  validTransitions: [],
  healthStatus: 'green',

  lastUpdated: null,

  setApiConnected: (ok) => set({ apiConnected: ok, lastUpdated: Date.now() }),
  setWsStatus: (s) => set({ wsStatus: s, lastUpdated: Date.now() }),
  setSystemState: (state, validTransitions) =>
    set({ systemState: state, validTransitions: validTransitions ?? [], lastUpdated: Date.now() }),
  setHealthStatus: (s) => set({ healthStatus: s, lastUpdated: Date.now() }),
  setError: (msg) => set({ lastError: msg, lastUpdated: Date.now() }),
  reset: () =>
    set({
      apiConnected: false,
      wsStatus: 'idle',
      lastError: null,
      systemState: 'BOOTING',
      validTransitions: [],
      healthStatus: 'green',
      lastUpdated: null,
    }),
}));
