import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Analytics } from '@/pages/Analytics/Analytics';

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="chart-container">{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  AreaChart: ({ children }: { children: React.ReactNode }) => <div data-testid="area-chart">{children}</div>,
  Area: () => null,
}));

describe('Analytics', () => {
  it('renders real-time metric charts', () => {
    renderWithRouter(<Analytics />);
    expect(screen.getByText('FPS')).toBeInTheDocument();
    expect(screen.getByText('GPU')).toBeInTheDocument();
    expect(screen.getByText('CPU')).toBeInTheDocument();
    expect(screen.getByText('Memory')).toBeInTheDocument();
    expect(screen.getByText('Latency')).toBeInTheDocument();
  });

  it('renders chart containers', () => {
    renderWithRouter(<Analytics />);
    const charts = screen.getAllByTestId('chart-container');
    expect(charts.length).toBeGreaterThan(0);
  });

  it('shows detection count metric', () => {
    renderWithRouter(<Analytics />);
    expect(screen.getByText('Detection Count')).toBeInTheDocument();
  });
});
