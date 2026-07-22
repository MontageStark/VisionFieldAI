import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import AppLayout from '@/components/layout/AppLayout';

const Dashboard = lazy(() => import('@/pages/Dashboard/Dashboard'));
const Camera = lazy(() => import('@/pages/Camera/Camera'));
const Servo = lazy(() => import('@/pages/Servo/Servo'));
const Director = lazy(() => import('@/pages/Director/Director'));
const Streaming = lazy(() => import('@/pages/Streaming/Streaming'));
const Replay = lazy(() => import('@/pages/Replay/Replay'));
const Health = lazy(() => import('@/pages/Health/Health'));
const Logs = lazy(() => import('@/pages/Logs/Logs'));
const Plugins = lazy(() => import('@/pages/Plugins/Plugins'));
const Calibration = lazy(() => import('@/pages/Calibration/Calibration'));
const Settings = lazy(() => import('@/pages/Settings/Settings'));
const VirtualCamera = lazy(() => import('@/pages/VirtualCamera'));
const Hardware = lazy(() => import('@/pages/Hardware'));
const Analytics = lazy(() => import('@/pages/Analytics/Analytics'));

function PageLoader() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
    </div>
  );
}

export default function App(): JSX.Element {
  return (
    <ErrorBoundary>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Suspense fallback={<PageLoader />}><Dashboard /></Suspense>} />
          <Route path="/camera" element={<Suspense fallback={<PageLoader />}><Camera /></Suspense>} />
          <Route path="/servo" element={<Suspense fallback={<PageLoader />}><Servo /></Suspense>} />
          <Route path="/director" element={<Suspense fallback={<PageLoader />}><Director /></Suspense>} />
          <Route path="/streaming" element={<Suspense fallback={<PageLoader />}><Streaming /></Suspense>} />
          <Route path="/replay" element={<Suspense fallback={<PageLoader />}><Replay /></Suspense>} />
          <Route path="/analytics" element={<Suspense fallback={<PageLoader />}><Analytics /></Suspense>} />
          <Route path="/health" element={<Suspense fallback={<PageLoader />}><Health /></Suspense>} />
          <Route path="/logs" element={<Suspense fallback={<PageLoader />}><Logs /></Suspense>} />
          <Route path="/plugins" element={<Suspense fallback={<PageLoader />}><Plugins /></Suspense>} />
          <Route path="/calibration" element={<Suspense fallback={<PageLoader />}><Calibration /></Suspense>} />
          <Route path="/settings" element={<Suspense fallback={<PageLoader />}><Settings /></Suspense>} />
          <Route path="/virtual-camera" element={<Suspense fallback={<PageLoader />}><VirtualCamera /></Suspense>} />
          <Route path="/hardware" element={<Suspense fallback={<PageLoader />}><Hardware /></Suspense>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}
