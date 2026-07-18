import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { VirtualCamera } from '@/pages/VirtualCamera/VirtualCamera';
import { fireEvent } from '@testing-library/react';

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

  it('updates zoom value on slider change', () => {
    renderWithRouter(<VirtualCamera />);
    const zoomSlider = screen.getAllByRole('slider')[0];
    fireEvent.change(zoomSlider, { target: { value: '3' } });
    expect(screen.getByText('3.0x')).toBeInTheDocument();
  });

  it('updates dead zone on slider change', () => {
    renderWithRouter(<VirtualCamera />);
    const deadZoneSlider = screen.getAllByRole('slider')[1];
    fireEvent.change(deadZoneSlider, { target: { value: '40' } });
    expect(screen.getByText('40%')).toBeInTheDocument();
  });

  it('updates motion speed on slider change', () => {
    renderWithRouter(<VirtualCamera />);
    const motionSlider = screen.getAllByRole('slider')[2];
    fireEvent.change(motionSlider, { target: { value: '75' } });
    expect(screen.getByText('75%')).toBeInTheDocument();
  });
});
