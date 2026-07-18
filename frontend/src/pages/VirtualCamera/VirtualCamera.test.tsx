import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { VirtualCamera } from '@/pages/VirtualCamera/VirtualCamera';

vi.mock('@/services/api', () => ({
  outputApi: {
    getState: vi.fn().mockResolvedValue({
      center_x: 0.5, center_y: 0.5, zoom: 1.5, mode: 'virtual',
    }),
    getMode: vi.fn().mockResolvedValue({ mode: 'virtual' }),
  },
}));

describe('VirtualCamera', () => {
  it('renders the interactive frame visualization', () => {
    renderWithRouter(<VirtualCamera />);
    expect(screen.getByTestId('virtual-camera-frame')).toBeInTheDocument();
  });

  it('displays zoom controls', () => {
    renderWithRouter(<VirtualCamera />);
    expect(screen.getByText('Zoom')).toBeInTheDocument();
  });

  it('displays dead zone slider', () => {
    renderWithRouter(<VirtualCamera />);
    expect(screen.getByText('Dead Zone')).toBeInTheDocument();
  });

  it('displays motion speed control', () => {
    renderWithRouter(<VirtualCamera />);
    expect(screen.getByText('Motion Speed')).toBeInTheDocument();
  });

  it('shows current zoom value', () => {
    renderWithRouter(<VirtualCamera />);
    expect(screen.getByText('1.5x')).toBeInTheDocument();
  });
});
