import { vi } from 'vitest';

// Make vitest's fake timers detectable by @testing-library/react's waitFor
if (typeof globalThis !== 'undefined') {
  (globalThis as Record<string, unknown>).jest = {
    advanceTimersByTime: (ms: number) => vi.advanceTimersByTime(ms),
    get current() {
      return {
        advanceTimersByTime: (ms: number) => vi.advanceTimersByTime(ms),
      };
    },
  };
}

import '@testing-library/jest-dom';
