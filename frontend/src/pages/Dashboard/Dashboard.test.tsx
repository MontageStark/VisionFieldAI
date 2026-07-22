import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen, waitFor } from '@/test/test-utils';
import { Dashboard } from '@/pages/Dashboard/Dashboard';

vi.mock('@/services/api', () => ({
  cameraApi: { status: vi.fn().mockResolvedValue({ running: true, uptime: 1800 }) },
  directorApi: {
    status: vi.fn().mockResolvedValue({
      mode: 'broadcast',
    }),
  },
}));

describe('Dashboard', () => {
  it('renders the live camera feed area', () => {
    renderWithRouter(<Dashboard />);
    expect(screen.getByTestId('live-camera-feed')).toBeInTheDocument();
  });

  it('renders AI Director panel', () => {
    renderWithRouter(<Dashboard />);
    expect(screen.getByText('AI Director')).toBeInTheDocument();
  });

  it('renders status cards for key metrics', () => {
    renderWithRouter(<Dashboard />);
    expect(screen.getByText('FPS')).toBeInTheDocument();
    expect(screen.getByText('Latency')).toBeInTheDocument();
    expect(screen.getByText('Players Detected')).toBeInTheDocument();
    expect(screen.getByText('GPU Usage')).toBeInTheDocument();
  });

  it('renders floating control buttons', () => {
    renderWithRouter(<Dashboard />);
    expect(screen.getByTestId('floating-controls')).toBeInTheDocument();
    expect(screen.getByText('Start')).toBeInTheDocument();
    expect(screen.getByText('Record')).toBeInTheDocument();
  });

  it('shows LIVE badge after data loads', async () => {
    renderWithRouter(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('LIVE')).toBeInTheDocument();
    });
  });
});
