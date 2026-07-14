import { NavLink } from 'react-router-dom';

interface NavItem {
  to: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: '🎛' },
  { to: '/camera', label: 'Camera', icon: '📷' },
  { to: '/servo', label: 'Servo', icon: '⚙' },
  { to: '/director', label: 'Director', icon: '🎬' },
  { to: '/streaming', label: 'Streaming', icon: '📡' },
  { to: '/replay', label: 'Replay', icon: '▶' },
  { to: '/health', label: 'Health', icon: '💚' },
  { to: '/logs', label: 'Logs', icon: '📋' },
  { to: '/plugins', label: 'Plugins', icon: '🧩' },
  { to: '/calibration', label: 'Calibration', icon: '🎯' },
  { to: '/settings', label: 'Settings', icon: '⚒' },
];

export function Sidebar(): JSX.Element {
  return (
    <aside className="flex w-60 flex-col border-r border-slate-800 bg-slate-950/80">
      <div className="flex h-16 items-center gap-2 border-b border-slate-800 px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white font-bold">
          FV
        </div>
        <span className="text-base font-semibold text-white">FieldVision</span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            <span className="text-lg" aria-hidden="true">
              {item.icon}
            </span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-slate-800 p-4 text-xs text-slate-500">
        v0.1.0 · Build skeleton
      </div>
    </aside>
  );
}

export default Sidebar;
