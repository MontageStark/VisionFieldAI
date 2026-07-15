import { create } from 'zustand';
import { outputApi } from '@/services/api';

export type OutputMode = 'virtual' | 'servo' | 'hybrid' | 'ptz';

export interface OutputState {
  center_x: number;
  center_y: number;
  zoom: number;
  mode: string;
}

export interface AppStoreState {
  outputMode: OutputMode;
  lastOutputState: OutputState | null;

  setOutputMode: (mode: OutputMode) => Promise<void>;
  fetchOutputState: () => Promise<void>;
}

export const useAppStore = create<AppStoreState>((set) => ({
  outputMode: 'virtual',
  lastOutputState: null,

  setOutputMode: async (mode) => {
    try {
      const response = await outputApi.setMode(mode);
      set({ outputMode: response.mode });
    } catch (error) {
      console.error('Failed to set output mode:', error);
    }
  },

  fetchOutputState: async () => {
    try {
      const response = await outputApi.getState();
      set({ lastOutputState: response });
    } catch (error) {
      console.error('Failed to fetch output state:', error);
    }
  },
}));
