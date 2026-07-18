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

  it('shows live indicator when tracking', () => {
    mockState.systemState = 'TRACKING';
    renderWithRouter(<Header />);
    expect(screen.getByTestId('live-indicator')).toBeInTheDocument();
  });

  it('does not show live indicator when idle', () => {
    mockState.systemState = 'IDLE';
    renderWithRouter(<Header />);
    expect(screen.queryByTestId('live-indicator')).not.toBeInTheDocument();
  });

  it('defaults to FieldVision AI for unknown route', () => {
    renderWithRouter(<Header />, { route: '/unknown' });
    expect(screen.getByText('FieldVision AI')).toBeInTheDocument();
  });

  it('falls back to ws status color for unknown ws state', () => {
    mockState.wsStatus = 'closed';
    renderWithRouter(<Header />);
    expect(screen.getByTestId('ws-status')).toBeInTheDocument();
  });

  it('shows WS connecting state', () => {
    mockState.wsStatus = 'connecting';
    renderWithRouter(<Header />);
    expect(screen.getByTestId('ws-status')).toBeInTheDocument();
  });

  it('shows WS error state', () => {
    mockState.wsStatus = 'error';
    renderWithRouter(<Header />);
    expect(screen.getByTestId('ws-status')).toBeInTheDocument();
  });

  it('shows default state color for unknown state', () => {
    mockState.systemState = 'BOOTING';
    renderWithRouter(<Header />);
    expect(screen.getByText('BOOTING')).toBeInTheDocument();
  });

  it('shows disconnected API status', () => {
    mockState.apiConnected = false;
    renderWithRouter(<Header />);
    expect(screen.getByTestId('api-status')).toBeInTheDocument();
  });
});
