import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Header } from '@/components/layout/Header';

const mockState = {
  apiConnected: true,
  wsStatus: 'open',
  systemState: 'IDLE',
};

vi.mock('@/stores/systemStore', () => ({
  useSystemStore: (selector?: (state: typeof mockState) => unknown) =>
    selector ? selector(mockState) : mockState,
}));

describe('Header', () => {
  beforeEach(() => {
    mockState.apiConnected = true;
    mockState.wsStatus = 'open';
    mockState.systemState = 'IDLE';
  });

  it('renders the page title from route', () => {
    renderWithRouter(<Header />, { route: '/camera' });
    expect(screen.getByText('Camera')).toBeInTheDocument();
  });

  it('shows API connection status', () => {
    renderWithRouter(<Header />);
    expect(screen.getByTestId('api-status')).toBeInTheDocument();
  });

  it('shows WebSocket connection status', () => {
    renderWithRouter(<Header />);
    expect(screen.getByTestId('ws-status')).toBeInTheDocument();
  });

  it('shows system state label', () => {
    renderWithRouter(<Header />);
    expect(screen.getByText('IDLE')).toBeInTheDocument();
  });

  it('shows live indicator when streaming', () => {
    mockState.systemState = 'STREAMING';
    renderWithRouter(<Header />);
    expect(screen.getByTestId('live-indicator')).toBeInTheDocument();
  });
});
