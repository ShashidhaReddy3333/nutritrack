/**
 * Auth store — in-memory only.
 *
 * The JWT lives in an httpOnly cookie managed by the server (Issue 6).
 * This store only tracks:
 *  - `user`:  the logged-in UserOut, populated by AuthInitializer on app load
 *  - `isInitialized`: whether /auth/me has been called yet (prevents flash redirects)
 */

import { create } from 'zustand';
import type { UserOut } from '../types';

interface AuthState {
  user: UserOut | null;
  isInitialized: boolean;
  setUser: (user: UserOut | null) => void;
  setInitialized: () => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isInitialized: false,
  setUser: (user) => set({ user }),
  setInitialized: () => set({ isInitialized: true }),
  logout: () => set({ user: null }),
}));
