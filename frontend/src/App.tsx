import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from '@/components/layout/AppLayout';
import Dashboard from '@/pages/Dashboard/Dashboard';
import Camera from '@/pages/Camera/Camera';
import Servo from '@/pages/Servo/Servo';
import Director from '@/pages/Director/Director';
import Streaming from '@/pages/Streaming/Streaming';
import Replay from '@/pages/Replay/Replay';
import Health from '@/pages/Health/Health';
import Logs from '@/pages/Logs/Logs';
import Plugins from '@/pages/Plugins/Plugins';
import Calibration from '@/pages/Calibration/Calibration';
import Settings from '@/pages/Settings/Settings';
import VirtualCamera from '@/pages/VirtualCamera';

export default function App(): JSX.Element {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/camera" element={<Camera />} />
        <Route path="/servo" element={<Servo />} />
        <Route path="/director" element={<Director />} />
        <Route path="/streaming" element={<Streaming />} />
        <Route path="/replay" element={<Replay />} />
        <Route path="/health" element={<Health />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/plugins" element={<Plugins />} />
        <Route path="/calibration" element={<Calibration />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/virtual-camera" element={<VirtualCamera />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
