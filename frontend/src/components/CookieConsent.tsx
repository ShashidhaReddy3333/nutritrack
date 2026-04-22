import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const STORAGE_KEY = 'nutritrack_cookie_notice_accepted';

export default function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(localStorage.getItem(STORAGE_KEY) !== 'true');
  }, []);

  if (!visible) return null;

  return (
    <div className="fixed inset-x-0 bottom-0 z-[60] border-t border-white/[0.08] bg-dark-900/95 backdrop-blur px-4 py-3">
      <div className="mx-auto flex max-w-5xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-gray-400">
          NutriTrack uses essential cookies for secure sign-in. Read the{' '}
          <Link to="/privacy" className="text-brand-400 hover:text-brand-300">Privacy Policy</Link>.
        </p>
        <button
          type="button"
          onClick={() => {
            localStorage.setItem(STORAGE_KEY, 'true');
            setVisible(false);
          }}
          className="btn-primary px-4 py-2 text-sm"
        >
          Accept
        </button>
      </div>
    </div>
  );
}
