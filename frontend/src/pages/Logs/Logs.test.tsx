import { describe, it, expect } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { Logs } from '@/pages/Logs/Logs';
import userEvent from '@testing-library/user-event';

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

  it('filters logs by Error level', async () => {
    const user = userEvent.setup();
    renderWithRouter(<Logs />);
    await user.click(screen.getByText('Error'));
    expect(screen.getByText('RTSP connection timeout')).toBeInTheDocument();
    expect(screen.queryByText('Application started')).not.toBeInTheDocument();
  });

  it('filters logs by Warning level', async () => {
    const user = userEvent.setup();
    renderWithRouter(<Logs />);
    await user.click(screen.getByText('Warning'));
    expect(screen.getByText('GPU usage above 80%')).toBeInTheDocument();
    expect(screen.queryByText('Application started')).not.toBeInTheDocument();
  });

  it('filters logs by Info level', async () => {
    const user = userEvent.setup();
    renderWithRouter(<Logs />);
    await user.click(screen.getByText('Info'));
    expect(screen.getByText('Application started')).toBeInTheDocument();
    expect(screen.queryByText('GPU usage above 80%')).not.toBeInTheDocument();
  });

  it('searches logs by message text', async () => {
    const user = userEvent.setup();
    renderWithRouter(<Logs />);
    await user.type(screen.getByPlaceholderText(/search logs/i), 'camera');
    expect(screen.getByText('Camera connected - 720p@15fps')).toBeInTheDocument();
    expect(screen.queryByText('GPU usage above 80%')).not.toBeInTheDocument();
  });

  it('restores all logs when search is cleared', async () => {
    const user = userEvent.setup();
    renderWithRouter(<Logs />);
    const searchInput = screen.getByPlaceholderText(/search logs/i);
    await user.type(searchInput, 'camera');
    await user.clear(searchInput);
    expect(screen.getByText('Application started')).toBeInTheDocument();
    expect(screen.getByText('GPU usage above 80%')).toBeInTheDocument();
  });
});
