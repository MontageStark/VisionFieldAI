import { describe, it, expect } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Streaming } from '@/pages/Streaming/Streaming';

describe('Streaming', () => {
  it('renders all destination cards', () => {
    renderWithRouter(<Streaming />);
    expect(screen.getByText('RTSP')).toBeInTheDocument();
    expect(screen.getByText('OBS')).toBeInTheDocument();
    expect(screen.getByText('YouTube')).toBeInTheDocument();
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
    expect(screen.getByText('Reconnect')).toBeInTheDocument();
  });
});
