import { lazy, Suspense, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Lenis from 'lenis';
import Layout from './components/Layout';

const LandingPage = lazy(() => import('./pages/LandingPage'));
const ExecutiveDashboard = lazy(() => import('./pages/ExecutiveDashboard'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const NotFound = lazy(() => import('./pages/NotFound'));
const CandidateManagement = lazy(() => import('./pages/CandidateManagement'));
const JobManagement = lazy(() => import('./pages/JobManagement'));
const Pipeline = lazy(() => import('./pages/Pipeline'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Settings = lazy(() => import('./pages/Settings'));
const FlaggedProfiles = lazy(() => import('./pages/FlaggedProfiles'));
const About = lazy(() => import('./pages/About'));

function PageFallback() {
  return <div className="min-h-screen bg-slate-50" aria-label="Loading page" />;
}

function App() {
  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      direction: 'vertical',
      gestureDirection: 'vertical',
      smooth: true,
      mouseMultiplier: 1,
      smoothTouch: false,
      touchMultiplier: 2,
      infinite: false,
    });

    let frameId;
    function raf(time) {
      lenis.raf(time);
      frameId = requestAnimationFrame(raf);
    }

    frameId = requestAnimationFrame(raf);

    return () => {
      cancelAnimationFrame(frameId);
      lenis.destroy();
    };
  }, []);

  return (
    <Suspense fallback={<PageFallback />}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Layout />}>
            <Route index element={<ExecutiveDashboard />} />
            <Route path="candidates" element={<CandidateManagement />} />
            <Route path="jobs" element={<JobManagement />} />
            <Route path="pipeline" element={<Pipeline />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="flagged" element={<FlaggedProfiles />} />
            <Route path="settings" element={<Settings />} />
            <Route path="about" element={<About />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </Suspense>
  );
}

export default App;
