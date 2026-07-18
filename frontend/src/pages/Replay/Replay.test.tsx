import { describe, it, expect } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Replay } from '@/pages/Replay/Replay';

describe('Replay', () => {
  it('renders the timeline component', () => {
    renderWithRouter(<Replay />);
    expect(screen.getByTestId('replay-timeline')).toBeInTheDocument();
  });

  it('shows event markers on timeline', () => {
    renderWithRouter(<Replay />);
    expect(screen.getByText('Goal')).toBeInTheDocument();
    expect(screen.getByText('Corner')).toBeInTheDocument();
    expect(screen.getByText('Throw')).toBeInTheDocument();
  });

  it('renders playback controls', () => {
    renderWithRouter(<Replay />);
    expect(screen.getByText('Replay')).toBeInTheDocument();
    expect(screen.getByText('Save Clip')).toBeInTheDocument();
    expect(screen.getByText('Export')).toBeInTheDocument();
  });
});
