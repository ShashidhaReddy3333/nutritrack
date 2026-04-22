import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register, getMe } from '../api/auth';
import { useAuthStore } from '../hooks/useAuth';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { setUser } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    if (password !== confirm) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    try {
      await register(email, password, acceptPrivacy);
      // After registration the server sets httpOnly cookies; fetch user info
      const meRes = await getMe();
      setUser(meRes.data);
      navigate('/profile/setup');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-900 flex">
      {/* Left panel — branding */}
      <div className="hidden md:flex md:w-1/2 bg-gradient-to-br from-dark-950 via-dark-900 to-brand-900/30 flex-col items-center justify-center p-12 relative overflow-hidden">
        <div className="absolute top-[-80px] left-[-80px] w-80 h-80 rounded-full bg-brand-500/5 blur-3xl" />
        <div className="absolute bottom-[-60px] right-[-60px] w-64 h-64 rounded-full bg-brand-400/8 blur-3xl" />

        <div className="relative z-10 max-w-sm text-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center shadow-glow-brand-lg mx-auto mb-8">
            <span className="text-white font-bold text-2xl">N</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-3">
            Your journey<br />
            <span className="gradient-text">starts here.</span>
          </h1>
          <p className="text-gray-400 text-base mb-10 leading-relaxed">
            Set up takes under 2 minutes. Tell us your goals and we'll build your personalized nutrition targets.
          </p>
          <div className="glass-card rounded-2xl p-5 text-left">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">What you get</p>
            <div className="space-y-2.5">
              {[
                { icon: '🎯', text: 'Personalized macro targets' },
                { icon: '🤖', text: 'AI-powered meal parsing' },
                { icon: '📊', text: 'Weekly nutrition trends' },
                { icon: '📄', text: 'PDF nutrition label extraction' },
              ].map(({ icon, text }) => (
                <div key={text} className="flex items-center gap-2.5">
                  <span className="text-base">{icon}</span>
                  <span className="text-gray-300 text-sm">{text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm animate-fade-up">
          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-8 md:hidden">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center shadow-glow-brand">
              <span className="text-white font-bold text-base">N</span>
            </div>
            <span className="text-xl font-bold text-white">NutriTrack</span>
          </div>

          <h2 className="text-2xl font-bold text-white mb-1">Create your account</h2>
          <p className="text-gray-400 text-sm mb-8">Free forever. No credit card required.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div role="alert" className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm flex items-start gap-2">
                <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                {error}
              </div>
            )}
            <div>
              <label htmlFor="reg-email" className="label-dark">Email address</label>
              <input
                id="reg-email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-dark"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label htmlFor="reg-password" className="label-dark">Password</label>
              <input
                id="reg-password"
                type="password"
                required
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-dark"
                placeholder="Min. 8 characters"
              />
            </div>
            <div>
              <label htmlFor="reg-confirm" className="label-dark">Confirm password</label>
              <input
                id="reg-confirm"
                type="password"
                required
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="input-dark"
                placeholder="••••••••"
              />
            </div>
            <label className="flex items-start gap-3 text-sm text-gray-400">
              <input
                type="checkbox"
                checked={acceptPrivacy}
                onChange={(e) => setAcceptPrivacy(e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-dark-600 bg-dark-700 text-brand-500 focus:ring-brand-500/40"
                required
              />
              <span>
                I agree to the{' '}
                <Link to="/privacy" className="text-brand-400 hover:text-brand-300">
                  Privacy Policy
                </Link>
                {' '}and{' '}
                <Link to="/terms" className="text-brand-400 hover:text-brand-300">
                  Terms of Service
                </Link>
                .
              </span>
            </label>
            <button
              type="submit"
              disabled={loading || !acceptPrivacy}
              className="btn-primary w-full mt-2 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Creating account…
                </>
              ) : 'Create account'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
