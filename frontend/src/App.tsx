import { lazy, Suspense, useEffect } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import CookieConsent from './components/CookieConsent';
import ProtectedRoute from './components/ProtectedRoute';
import { getMe, refreshToken } from './api/auth';
import { useAuthStore } from './hooks/useAuth';

const queryClient = new QueryClient();

const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage'));
const TermsPage = lazy(() => import('./pages/TermsPage'));
const ProfileSetupPage = lazy(() => import('./pages/ProfileSetupPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const HistoryPage = lazy(() => import('./pages/HistoryPage'));
const ProductsPage = lazy(() => import('./pages/ProductsPage'));
const LogMealPage = lazy(() => import('./pages/LogMealPage'));

function PageFallback() {
  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center">
      <svg className="animate-spin w-7 h-7 text-brand-500" aria-label="Loading" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>
  );
}

function AuthInitializer() {
  const { setUser, setInitialized } = useAuthStore();

  useEffect(() => {
    getMe()
      .catch(async () => {
        await refreshToken();
        return getMe();
      })
      .then((res) => setUser(res.data))
      .catch(() => setUser(null))
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
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/terms" element={<TermsPage />} />

            <Route path="/profile/setup" element={<ProtectedRoute><ProfileSetupPage /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
            <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
            <Route path="/history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
            <Route path="/products" element={<ProtectedRoute><ProductsPage /></ProtectedRoute>} />
            <Route path="/log" element={<ProtectedRoute><LogMealPage /></ProtectedRoute>} />

            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route
              path="*"
              element={
                <div className="min-h-screen bg-dark-900 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-6xl font-bold text-gray-700 mb-4">404</div>
                    <div className="text-gray-400 mb-6">Page not found</div>
                    <a href="/dashboard" className="text-brand-400 hover:text-brand-300 transition-colors">
                      Go to Dashboard
                    </a>
                  </div>
                </div>
              }
            />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
