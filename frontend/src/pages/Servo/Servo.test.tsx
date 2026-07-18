import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Servo } from '@/pages/Servo/Servo';

vi.mock('@/services/api', () => ({
  servoApi: {
    status: vi.fn().mockResolvedValue({
      pan_angle: 90, tilt_angle: 90, emergency_stop: false,
    }),
    command: vi.fn().mockResolvedValue({ status: 'ok' }),
    home: vi.fn().mockResolvedValue({ status: 'homed' }),
    emergency: vi.fn().mockResolvedValue({ status: 'emergency_stop_activated' }),
  },
  outputApi: {
    getMode: vi.fn().mockResolvedValue({ mode: 'servo' }),
  },
}));

describe('Servo', () => {
  it('shows servo connected status', () => {
    renderWithRouter(<Servo />);
    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  it('displays current angle', () => {
    renderWithRouter(<Servo />);
    expect(screen.getByText('90°')).toBeInTheDocument();
  });

  it('renders calibration wizard', () => {
    renderWithRouter(<Servo />);
    expect(screen.getByText('Center')).toBeInTheDocument();
    expect(screen.getByText('Left Limit')).toBeInTheDocument();
    expect(screen.getByText('Right Limit')).toBeInTheDocument();
    expect(screen.getByText('Save')).toBeInTheDocument();
  });

  it('renders action buttons', () => {
    renderWithRouter(<Servo />);
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Emergency Stop')).toBeInTheDocument();
  });
});
