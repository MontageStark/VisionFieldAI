import { useState } from 'react';
import { Bell, CheckCircle, AlertTriangle, XCircle, X } from 'lucide-react';

interface Notification {
  id: string;
  type: 'success' | 'warning' | 'error';
  message: string;
  timestamp: number;
}

const mockNotifications: Notification[] = [
  { id: '1', type: 'success', message: 'Stream Started', timestamp: Date.now() },
  { id: '2', type: 'success', message: 'Goal Detected', timestamp: Date.now() },
  { id: '3', type: 'warning', message: 'High GPU Usage', timestamp: Date.now() },
  { id: '4', type: 'error', message: 'Low FPS', timestamp: Date.now() },
];

function iconForType(type: string) {
  switch (type) {
    case 'success': return <CheckCircle size={16} className="text-accent-success" />;
    case 'warning': return <AlertTriangle size={16} className="text-accent-warning" />;
    case 'error': return <XCircle size={16} className="text-accent-error" />;
    default: return <Bell size={16} />;
  }
}

export function NotificationCenter(): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications] = useState<Notification[]>(mockNotifications);

  return (
    <div className="relative">
      <button
        data-testid="notification-trigger"
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-dark-card text-slate-400 hover:text-white transition-colors"
      >
        <Bell size={20} />
        {notifications.length > 0 && (
          <span
            data-testid="notification-count"
            className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-accent-error text-[10px] font-bold text-white"
          >
            {notifications.length}
          </span>
        )}
      </button>

      <div className={`absolute right-0 top-12 w-80 rounded-xl border border-dark-border bg-dark-card shadow-2xl z-50 ${isOpen ? 'block' : 'hidden'}`}>
        <div className="flex items-center justify-between border-b border-dark-border p-3">
          <span className="text-sm font-semibold text-white">Notifications</span>
          <button type="button" onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white">
            <X size={16} />
          </button>
        </div>
        <div className="max-h-64 overflow-y-auto">
          {notifications.map((n) => (
            <div
              key={n.id}
              data-testid={`notification-${n.type}`}
              className="flex items-center gap-3 border-b border-dark-border/50 p-3 last:border-0"
            >
              {iconForType(n.type)}
              <span className="text-sm text-slate-200">{n.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default NotificationCenter;
