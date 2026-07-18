import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Director } from '@/pages/Director/Director';

vi.mock('@/services/api', () => ({
  directorApi: {
    status: vi.fn().mockResolvedValue({
      mode: 'broadcast',
      last_decision: {
        mode: 'broadcast',
        confidence: 0.95,
        reasoning: 'Ball near penalty area, zooming in',
        target: { center_x: 0.7, center_y: 0.4, zoom: 2.0 },
      },
    }),
    setMode: vi.fn().mockResolvedValue({ status: 'ok' }),
  },
}));

describe('Director', () => {
  it('renders all director mode options', () => {
    renderWithRouter(<Director />);
    expect(screen.getByText('Broadcast')).toBeInTheDocument();
    expect(screen.getByText('Aggressive')).toBeInTheDocument();
    expect(screen.getByText('Wide')).toBeInTheDocument();
    expect(screen.getByText('Training')).toBeInTheDocument();
    expect(screen.getByText('Manual Assist')).toBeInTheDocument();
  });

  it('displays the current decision in human-readable format', async () => {
    renderWithRouter(<Director />);
    expect(screen.getByText('Current Decision')).toBeInTheDocument();
    expect(screen.getByText(/Ball near penalty area/)).toBeInTheDocument();
  });

  it('shows confidence as percentage', async () => {
    renderWithRouter(<Director />);
    expect(screen.getByText('95%')).toBeInTheDocument();
  });

  it('shows zoom level', async () => {
    renderWithRouter(<Director />);
    expect(screen.getByText('2.0x')).toBeInTheDocument();
  });

  it('highlights the active mode', async () => {
    renderWithRouter(<Director />);
    const broadcastBtn = screen.getByText('Broadcast').closest('button');
    expect(broadcastBtn).toHaveAttribute('data-active', 'true');
  });
});
