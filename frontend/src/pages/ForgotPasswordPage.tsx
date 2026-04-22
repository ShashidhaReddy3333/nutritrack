import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { forgotPassword } from '../api/auth';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setMessage('');
    setError('');
    setLoading(true);
    try {
      await forgotPassword(email);
      setMessage('If that email is registered, a password reset link has been sent.');
    } catch {
      setError('Password reset is temporarily unavailable. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-sm animate-fade-up">
        <Link to="/login" className="text-sm text-gray-500 hover:text-gray-300 transition-colors">
          Back to sign in
        </Link>
        <h1 className="text-2xl font-bold text-white mt-6 mb-1">Reset your password</h1>
        <p className="text-gray-400 text-sm mb-8">Enter your email and we will send a reset link.</p>

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
            <label htmlFor="forgot-email" className="label-dark">Email address</label>
            <input
              id="forgot-email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-dark"
              placeholder="you@example.com"
            />
          </div>
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Sending...' : 'Send reset link'}
          </button>
        </form>
      </div>
    </div>
  );
}
