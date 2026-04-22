/**
 * ProtectedRoute — guards against unauthenticated access.
 *
 * Does NOT check localStorage (removed — Issue 6).
 * Waits for AuthInitializer to call /auth/me before deciding whether to redirect.
 * This prevents the flash-to-login problem for users with valid cookies (Issue 21).
 */

import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuth';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isInitialized } = useAuthStore();

  // Still waiting for /auth/me — show nothing to prevent flash redirect
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <svg className="animate-spin w-8 h-8 text-brand-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
