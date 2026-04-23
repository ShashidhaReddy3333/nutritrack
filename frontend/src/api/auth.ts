import api from './client';
import type { SessionResponse, UserOut } from '../types';

export const register = (email: string, password: string, accept_privacy: boolean) =>
  api.post<SessionResponse>('/auth/register', { email, password, accept_privacy });

export const login = (email: string, password: string) =>
  api.post<SessionResponse>('/auth/login', { email, password });

export const logout = () => api.post('/auth/logout');

export const refreshToken = () => api.post<SessionResponse>('/auth/refresh');

export const getMe = () => api.get<UserOut>('/auth/me');

export const forgotPassword = (email: string) =>
  api.post('/auth/forgot-password', { email });

export const resetPassword = (token: string, new_password: string) =>
  api.post('/auth/reset-password', { token, new_password });
