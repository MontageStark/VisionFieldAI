import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen } from '@/test/test-utils';
import { NotificationCenter } from '@/components/notifications/NotificationCenter';

const mockNotifications = [
  { id: '1', type: 'success' as const, message: 'Stream Started', timestamp: Date.now() },
  { id: '2', type: 'success' as const, message: 'Goal Detected', timestamp: Date.now() },
  { id: '3', type: 'warning' as const, message: 'High GPU Usage', timestamp: Date.now() },
  { id: '4', type: 'error' as const, message: 'Low FPS', timestamp: Date.now() },
];

vi.mock('@/stores/notificationStore', () => ({
  useNotificationStore: () => ({
    notifications: mockNotifications,
    markAsRead: vi.fn(),
    clearAll: vi.fn(),
  }),
}));

describe('NotificationCenter', () => {
  it('renders notification count badge', () => {
    renderWithRouter(<NotificationCenter />);
    expect(screen.getByTestId('notification-count')).toHaveTextContent('4');
  });

  it('displays notifications in dropdown', async () => {
    renderWithRouter(<NotificationCenter />);
    screen.getByTestId('notification-trigger').click();
    expect(screen.getByText('Stream Started')).toBeInTheDocument();
    expect(screen.getByText('Goal Detected')).toBeInTheDocument();
    expect(screen.getByText('High GPU Usage')).toBeInTheDocument();
  });

  it('shows success notifications with green icon', async () => {
    renderWithRouter(<NotificationCenter />);
    screen.getByTestId('notification-trigger').click();
    const successItems = screen.getAllByTestId('notification-success');
    expect(successItems.length).toBe(2);
  });

  it('shows warning notifications with yellow icon', async () => {
    renderWithRouter(<NotificationCenter />);
    screen.getByTestId('notification-trigger').click();
    const warningItems = screen.getAllByTestId('notification-warning');
    expect(warningItems.length).toBe(1);
  });
});
