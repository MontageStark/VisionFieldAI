import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { FloatingControls } from '@/components/controls/FloatingControls';

vi.mock('@/services/api', () => ({
  cameraApi: {
    start: vi.fn().mockResolvedValue({ status: 'started' }),
    stop: vi.fn().mockResolvedValue({ status: 'stopped' }),
  },
  streamApi: {
    start: vi.fn().mockResolvedValue({ status: 'started' }),
    stop: vi.fn().mockResolvedValue({ status: 'stopped' }),
  },
}));

describe('FloatingControls', () => {
  it('renders all control buttons', () => {
    renderWithRouter(<FloatingControls />);
    expect(screen.getByText('Start')).toBeInTheDocument();
    expect(screen.getByText('Stop')).toBeInTheDocument();
    expect(screen.getByText('Snapshot')).toBeInTheDocument();
    expect(screen.getByText('Record')).toBeInTheDocument();
  });

  it('renders settings button', () => {
    renderWithRouter(<FloatingControls />);
    expect(screen.getByTestId('floating-settings')).toBeInTheDocument();
  });

  it('buttons have correct icons', () => {
    renderWithRouter(<FloatingControls />);
    expect(screen.getByTestId('btn-start')).toBeInTheDocument();
    expect(screen.getByTestId('btn-stop')).toBeInTheDocument();
    expect(screen.getByTestId('btn-snapshot')).toBeInTheDocument();
    expect(screen.getByTestId('btn-record')).toBeInTheDocument();
  });
});
