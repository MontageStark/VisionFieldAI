import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export function AppLayout(): JSX.Element {
  return (
    <div className="flex h-full">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-auto bg-slate-950 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
