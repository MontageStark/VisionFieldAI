import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Settings } from '@/pages/Settings/Settings';

vi.mock('@/stores/appStore', () => ({
  useAppStore: () => ({
    outputMode: 'virtual',
    setOutputMode: vi.fn(),
  }),
}));

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
    renderWithRouter(<Settings />);
    const aiTab = screen.getByText('AI');
    aiTab.click();
    expect(screen.getByText('Detection Model')).toBeInTheDocument();
    expect(screen.getByText('YOLO11')).toBeInTheDocument();
  });

  it('shows AI settings with model options', async () => {
    renderWithRouter(<Settings />);
    screen.getByText('AI').click();
    expect(screen.getByText('Tracker')).toBeInTheDocument();
    expect(screen.getByText('ByteTrack')).toBeInTheDocument();
    expect(screen.getByText('Motion Style')).toBeInTheDocument();
    expect(screen.getByText('Aggressiveness')).toBeInTheDocument();
  });
});
