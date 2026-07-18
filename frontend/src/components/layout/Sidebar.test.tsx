import { describe, it, expect } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Sidebar } from '@/components/layout/Sidebar';

describe('Sidebar', () => {
  it('renders all navigation items', () => {
    renderWithRouter(<Sidebar />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Camera')).toBeInTheDocument();
    expect(screen.getByText('AI Director')).toBeInTheDocument();
    expect(screen.getByText('Streaming')).toBeInTheDocument();
    expect(screen.getByText('Hardware')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    expect(screen.getByText('Replay')).toBeInTheDocument();
    expect(screen.getByText('Recording')).toBeInTheDocument();
    expect(screen.getByText('Matches')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Logs')).toBeInTheDocument();
  });

  it('renders the FieldVision AI logo', () => {
    renderWithRouter(<Sidebar />);
    expect(screen.getByText('FieldVision AI')).toBeInTheDocument();
  });

  it('highlights the active route', () => {
    renderWithRouter(<Sidebar />, { route: '/camera' });
    const cameraLink = screen.getByText('Camera').closest('a');
    expect(cameraLink).toHaveClass('active');
  });

  it('renders navigation links with correct hrefs', () => {
    renderWithRouter(<Sidebar />);
    expect(screen.getByText('Dashboard').closest('a')).toHaveAttribute('href', '/');
    expect(screen.getByText('Camera').closest('a')).toHaveAttribute('href', '/camera');
    expect(screen.getByText('AI Director').closest('a')).toHaveAttribute('href', '/director');
    expect(screen.getByText('Streaming').closest('a')).toHaveAttribute('href', '/streaming');
    expect(screen.getByText('Settings').closest('a')).toHaveAttribute('href', '/settings');
    expect(screen.getByText('Logs').closest('a')).toHaveAttribute('href', '/logs');
  });
});
