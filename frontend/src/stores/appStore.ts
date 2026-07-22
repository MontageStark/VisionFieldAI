import { create } from 'zustand';
import { outputApi } from '@/services/api';

export type OutputMode = 'virtual' | 'servo' | 'hybrid' | 'ptz';

export interface AppStoreState {
  outputMode: OutputMode;
  setOutputMode: (mode: OutputMode) => Promise<void>;
}

export const useAppStore = create<AppStoreState>((set) => ({
  outputMode: 'virtual',

  setOutputMode: async (mode) => {
    try {
      const response = await outputApi.setMode(mode);
      set({ outputMode: response.mode });
    } catch (error) {
      console.error('Failed to set output mode:', error);
    }
  },
}));
