import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, Camera, Clapperboard, Radio, 
  Settings, BarChart3, PlayCircle, CircleDot, 
  Trophy, ScrollText, MonitorCog
} from 'lucide-react';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  end?: boolean;
}

const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: <LayoutDashboard size={18} />, end: true },
  { to: '/camera', label: 'Camera', icon: <Camera size={18} /> },
  { to: '/director', label: 'AI Director', icon: <Clapperboard size={18} /> },
  { to: '/streaming', label: 'Streaming', icon: <Radio size={18} /> },
  { to: '/servo', label: 'Hardware', icon: <MonitorCog size={18} /> },
  { to: '/analytics', label: 'Analytics', icon: <BarChart3 size={18} /> },
  { to: '/replay', label: 'Replay', icon: <PlayCircle size={18} /> },
  { to: '/recording', label: 'Recording', icon: <CircleDot size={18} /> },
  { to: '/matches', label: 'Matches', icon: <Trophy size={18} /> },
  { to: '/settings', label: 'Settings', icon: <Settings size={18} /> },
  { to: '/logs', label: 'Logs', icon: <ScrollText size={18} /> },
];

export function Sidebar(): JSX.Element {
  return (
    <aside className="flex w-60 flex-col border-r border-dark-border bg-dark-surface" data-testid="sidebar">
      <div className="flex h-16 items-center gap-2 border-b border-dark-border px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-500 text-white font-bold">
          FV
        </div>
        <span className="text-base font-semibold text-white">FieldVision AI</span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'active bg-primary-500/10 text-primary-400'
                  : 'text-slate-400 hover:bg-dark-card hover:text-slate-200'
              }`
            }
          >
            <span aria-hidden="true">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-dark-border p-4 text-xs text-slate-500">
        v1.0.0 · Broadcast Control
      </div>
    </aside>
  );
}

export default Sidebar;
