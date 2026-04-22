import { FormEvent, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { resetPassword } from '../api/auth';

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setMessage('');
    setError('');
    if (!token) {
      setError('This reset link is missing a token.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      await resetPassword(token, password);
      setMessage('Password reset complete. You can now sign in.');
      setPassword('');
      setConfirm('');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Could not reset password. The link may be expired.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-sm animate-fade-up">
        <h1 className="text-2xl font-bold text-white mb-1">Choose a new password</h1>
        <p className="text-gray-400 text-sm mb-8">Use at least 8 characters.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {message && (
            <div role="status" className="bg-brand-500/10 border border-brand-500/30 text-brand-300 rounded-xl px-4 py-3 text-sm">
              {message}
            </div>
          )}
          {error && (
            <div role="alert" className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm">
              {error}
            </div>
          )}
          <div>
            <label htmlFor="reset-password" className="label-dark">New password</label>
            <input
              id="reset-password"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-dark"
            />
          </div>
          <div>
            <label htmlFor="reset-confirm" className="label-dark">Confirm password</label>
            <input
              id="reset-confirm"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className="input-dark"
            />
          </div>
          <button type="submit" disabled={loading || !token} className="btn-primary w-full">
            {loading ? 'Saving...' : 'Reset password'}
          </button>
        </form>
        <p className="text-center text-sm text-gray-500 mt-6">
          <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
