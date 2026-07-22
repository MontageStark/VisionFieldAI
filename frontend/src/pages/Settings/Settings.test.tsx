import { describe, it, expect } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Settings } from '@/pages/Settings/Settings';
import userEvent from '@testing-library/user-event';

describe('Settings', () => {
  it('renders all setting tabs', () => {
    renderWithRouter(<Settings />);
    expect(screen.getByText('General')).toBeInTheDocument();
    expect(screen.getByText('Camera')).toBeInTheDocument();
    expect(screen.getByText('AI')).toBeInTheDocument();
    expect(screen.getByText('Virtual Camera')).toBeInTheDocument();
    expect(screen.getByText('Servo')).toBeInTheDocument();
    expect(screen.getByText('Streaming')).toBeInTheDocument();
    expect(screen.getByText('OBS')).toBeInTheDocument();
    expect(screen.getByText('Notifications')).toBeInTheDocument();
  });

  it('defaults to General tab', () => {
    renderWithRouter(<Settings />);
    expect(screen.getByText('General Settings')).toBeInTheDocument();
  });

  it('switches tabs on click', async () => {
    const user = userEvent.setup();
    renderWithRouter(<Settings />);
    await user.click(screen.getByRole('tab', { name: 'AI' }));
    expect(screen.getByText('Detection Model')).toBeInTheDocument();
    expect(screen.getByText('YOLO11')).toBeInTheDocument();
  });

  it('shows AI settings with model options', async () => {
    const user = userEvent.setup();
    renderWithRouter(<Settings />);
    await user.click(screen.getByRole('tab', { name: 'AI' }));
    expect(screen.getByText('Tracker')).toBeInTheDocument();
    expect(screen.getByText('ByteTrack')).toBeInTheDocument();
    expect(screen.getByText('Motion Style')).toBeInTheDocument();
    expect(screen.getByText('Aggressiveness')).toBeInTheDocument();
  });

  it('has accessible tab roles', () => {
    renderWithRouter(<Settings />);
    const tablist = screen.getByRole('tablist');
    expect(tablist).toBeInTheDocument();
    const tabs = screen.getAllByRole('tab');
    expect(tabs.length).toBe(8);
  });
});
