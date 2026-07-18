import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Streaming } from '@/pages/Streaming/Streaming';

vi.mock('@/services/api', () => ({
  streamApi: {
    status: vi.fn().mockResolvedValue({ streaming: true, uptime: 600 }),
    start: vi.fn().mockResolvedValue({ status: 'started' }),
    stop: vi.fn().mockResolvedValue({ status: 'stopped' }),
  },
}));

describe('Streaming', () => {
  it('renders all destination status cards', () => {
    renderWithRouter(<Streaming />);
    expect(screen.getByText('RTSP')).toBeInTheDocument();
    expect(screen.getByText('OBS')).toBeInTheDocument();
    expect(screen.getByText('YouTube')).toBeInTheDocument();
  });

  it('displays connection status for each destination', () => {
    renderWithRouter(<Streaming />);
    const connectedBadges = screen.getAllByText('Connected');
    expect(connectedBadges.length).toBeGreaterThanOrEqual(1);
  });

  it('shows stream metrics', () => {
    renderWithRouter(<Streaming />);
    expect(screen.getByText('Dropped Frames')).toBeInTheDocument();
    expect(screen.getByText('Bitrate')).toBeInTheDocument();
    expect(screen.getByText('Latency')).toBeInTheDocument();
  });

  it('renders action buttons', () => {
    renderWithRouter(<Streaming />);
    expect(screen.getByText('Go Live')).toBeInTheDocument();
    expect(screen.getByText('Stop')).toBeInTheDocument();
    expect(screen.getByText('Reconnect')).toBeInTheDocument();
  });
});
