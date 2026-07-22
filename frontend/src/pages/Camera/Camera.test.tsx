import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen, waitFor } from '@/test/test-utils';
import { Camera } from '@/pages/Camera/Camera';

vi.mock('@/services/api', () => ({
  cameraApi: {
    status: vi.fn().mockResolvedValue({ running: true, uptime: 120 }),
    start: vi.fn().mockResolvedValue({ status: 'started' }),
    stop: vi.fn().mockResolvedValue({ status: 'stopped' }),
  },
}));

describe('Camera', () => {
  it('renders camera info cards', () => {
    renderWithRouter(<Camera />);
    expect(screen.getByText('Input Source')).toBeInTheDocument();
    expect(screen.getByText('Resolution')).toBeInTheDocument();
    expect(screen.getByText('FPS')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('shows camera status after loading', async () => {
    renderWithRouter(<Camera />);
    await waitFor(() => {
      expect(screen.getByText('Running')).toBeInTheDocument();
    });
  });

  it('renders action buttons', () => {
    renderWithRouter(<Camera />);
    expect(screen.getByText('Reconnect')).toBeInTheDocument();
    expect(screen.getByText('Snapshot')).toBeInTheDocument();
    expect(screen.getByText('Calibrate')).toBeInTheDocument();
    expect(screen.getByText('Reset')).toBeInTheDocument();
  });
});
