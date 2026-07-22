import { describe, it, expect } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Logs } from '@/pages/Logs/Logs';

describe('Logs', () => {
  it('renders the log viewer', () => {
    renderWithRouter(<Logs />);
    expect(screen.getByTestId('log-viewer')).toBeInTheDocument();
  });

  it('shows log level filter', () => {
    renderWithRouter(<Logs />);
    expect(screen.getByText('Level')).toBeInTheDocument();
    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(screen.getByText('Info')).toBeInTheDocument();
  });

  it('shows component filter', () => {
    renderWithRouter(<Logs />);
    expect(screen.getByText('Component')).toBeInTheDocument();
  });

  it('has a search input', () => {
    renderWithRouter(<Logs />);
    expect(screen.getByPlaceholderText(/search logs/i)).toBeInTheDocument();
  });

  it('shows empty state when no logs', () => {
    renderWithRouter(<Logs />);
    expect(screen.getByText('No log entries yet')).toBeInTheDocument();
    expect(screen.getByText('Start the system to see real-time logs')).toBeInTheDocument();
  });

  it('has accessible search input', () => {
    renderWithRouter(<Logs />);
    expect(screen.getByLabelText('Search logs')).toBeInTheDocument();
  });
});
