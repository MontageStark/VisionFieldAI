import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Dashboard } from '@/pages/Dashboard/Dashboard';

vi.mock('@/stores/systemStore', () => ({
  useSystemStore: () => ({
    systemState: 'TRACKING',
    healthStatus: 'green',
    lastError: null,
    apiConnected: true,
    wsStatus: 'open',
  }),
}));

vi.mock('@/services/api', () => ({
  systemApi: { health: vi.fn().mockResolvedValue({ status: 'healthy', uptime: 3600 }) },
  cameraApi: { status: vi.fn().mockResolvedValue({ running: true, uptime: 1800 }) },
  directorApi: { decision: vi.fn().mockResolvedValue({
    mode: 'broadcast',
    confidence: 0.98,
    reasoning: 'High player density moving toward goal',
    target: { center_x: 0.6, center_y: 0.5, zoom: 1.8 },
  })},
  streamApi: { status: vi.fn().mockResolvedValue({ streaming: true, uptime: 900 }) },
}));

describe('Dashboard', () => {
  it('renders the live camera feed area', () => {
    renderWithRouter(<Dashboard />);
    expect(screen.getByTestId('live-camera-feed')).toBeInTheDocument();
  });

  it('renders AI Director decision panel', () => {
    renderWithRouter(<Dashboard />);
    expect(screen.getByText('AI Director')).toBeInTheDocument();
    expect(screen.getByText('Current Decision')).toBeInTheDocument();
  });

  it('displays director reasoning in human-readable format', async () => {
    renderWithRouter(<Dashboard />);
    expect(screen.getByText(/High player density/)).toBeInTheDocument();
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

  it('shows system state as a badge', () => {
    renderWithRouter(<Dashboard />);
    expect(screen.getByText('TRACKING')).toBeInTheDocument();
  });
});
