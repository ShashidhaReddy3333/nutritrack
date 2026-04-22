import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';
import ProfileSetupPage from './pages/ProfileSetupPage';
import ProfilePage from './pages/ProfilePage';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import ProductsPage from './pages/ProductsPage';
import LogMealPage from './pages/LogMealPage';
import ProtectedRoute from './components/ProtectedRoute';
import CookieConsent from './components/CookieConsent';
import { useAuthStore } from './hooks/useAuth';
import { getMe } from './api/auth';

const queryClient = new QueryClient();

/**
 * AuthInitializer — runs once on mount, calls /auth/me to verify the httpOnly cookie.
 * Sets `user` in the store if authenticated, then marks `isInitialized = true`.
 * This prevents ProtectedRoute from flashing to /login for users with valid sessions (Issue 21).
 */
function AuthInitializer() {
  const { setUser, setInitialized } = useAuthStore();

  useEffect(() => {
    getMe()
      .then((res) => setUser(res.data))
      .catch(() => setUser(null))  // 401 or network error — treat as unauthenticated
      .finally(() => setInitialized());
  }, [setUser, setInitialized]);

  return null;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthInitializer />
        <CookieConsent />
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/terms" element={<TermsPage />} />

          {/* Protected */}
          <Route path="/profile/setup" element={
            <ProtectedRoute><ProfileSetupPage /></ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute><ProfilePage /></ProtectedRoute>
          } />
          <Route path="/dashboard" element={
            <ProtectedRoute><DashboardPage /></ProtectedRoute>
          } />
          <Route path="/history" element={
            <ProtectedRoute><HistoryPage /></ProtectedRoute>
          } />
          <Route path="/products" element={
            <ProtectedRoute><ProductsPage /></ProtectedRoute>
          } />
          <Route path="/log" element={
            <ProtectedRoute><LogMealPage /></ProtectedRoute>
          } />

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          {/* Catch-all — show 404 instead of silently redirecting (Issue 37) */}
          <Route path="*" element={
            <div className="min-h-screen bg-dark-900 flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl font-bold text-gray-700 mb-4">404</div>
                <div className="text-gray-400 mb-6">Page not found</div>
                <a href="/dashboard" className="text-brand-400 hover:text-brand-300 transition-colors">
                  Go to Dashboard
                </a>
              </div>
            </div>
          } />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
