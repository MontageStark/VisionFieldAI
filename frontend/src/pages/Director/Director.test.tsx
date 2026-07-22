import { describe, it, expect } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Director } from '@/pages/Director/Director';
import userEvent from '@testing-library/user-event';

describe('Director', () => {
  it('renders all director mode options', () => {
    renderWithRouter(<Director />);
    expect(screen.getByText('Broadcast')).toBeInTheDocument();
    expect(screen.getByText('Aggressive')).toBeInTheDocument();
    expect(screen.getByText('Wide')).toBeInTheDocument();
    expect(screen.getByText('Training')).toBeInTheDocument();
    expect(screen.getByText('Manual Assist')).toBeInTheDocument();
  });

  it('shows current decision placeholder', () => {
    renderWithRouter(<Director />);
    expect(screen.getByText('Current Decision')).toBeInTheDocument();
    expect(screen.getByText('Waiting for live director data...')).toBeInTheDocument();
  });

  it('highlights the active mode', () => {
    renderWithRouter(<Director />);
    const broadcastBtn = screen.getByText('Broadcast').closest('button');
    expect(broadcastBtn).toHaveAttribute('data-active', 'true');
  });

  it('switches mode on click', async () => {
    const user = userEvent.setup();
    renderWithRouter(<Director />);
    await user.click(screen.getByText('Aggressive').closest('button')!);
    const aggressiveBtn = screen.getByText('Aggressive').closest('button');
    expect(aggressiveBtn).toHaveAttribute('data-active', 'true');
    const broadcastBtn = screen.getByText('Broadcast').closest('button');
    expect(broadcastBtn).toHaveAttribute('data-active', 'false');
  });
});
