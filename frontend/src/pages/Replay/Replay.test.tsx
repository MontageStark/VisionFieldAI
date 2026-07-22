import { describe, it, expect } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Replay } from '@/pages/Replay/Replay';

describe('Replay', () => {
  it('renders the timeline component', () => {
    renderWithRouter(<Replay />);
    expect(screen.getByTestId('replay-timeline')).toBeInTheDocument();
  });

  it('shows empty state when no recording data', () => {
    renderWithRouter(<Replay />);
    expect(screen.getByText('No recording data')).toBeInTheDocument();
    expect(screen.getByText('Start a recording to see events here')).toBeInTheDocument();
  });

  it('renders playback controls', () => {
    renderWithRouter(<Replay />);
    expect(screen.getByText('Replay')).toBeInTheDocument();
    expect(screen.getByText('Save Clip')).toBeInTheDocument();
    expect(screen.getByText('Export')).toBeInTheDocument();
  });
});
