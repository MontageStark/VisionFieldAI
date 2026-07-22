import { create } from 'zustand';
import type { SystemState } from '@/types/api';

export interface SystemStoreState {
  apiConnected: boolean;
  wsStatus: 'idle' | 'connecting' | 'open' | 'closed' | 'error';
  systemState: SystemState;

  setApiConnected: (ok: boolean) => void;
  setWsStatus: (s: SystemStoreState['wsStatus']) => void;
  setSystemState: (state: SystemState) => void;
}

export const useSystemStore = create<SystemStoreState>((set) => ({
  apiConnected: false,
  wsStatus: 'idle',
  systemState: 'BOOTING',

  setApiConnected: (ok) => set({ apiConnected: ok }),
  setWsStatus: (s) => set({ wsStatus: s }),
  setSystemState: (state) => set({ systemState: state }),
}));
