import api from './client';
import type { ProfileOut, ProfileCreate, ProfileUpdate, DailyTargets } from '../types';

export const createProfile = (data: ProfileCreate) =>
  api.post<ProfileOut>('/profile', data);

export const getProfile = () => api.get<ProfileOut>('/profile');

export const updateProfile = (data: ProfileUpdate) =>
  api.patch<ProfileOut>('/profile', data);

export const getTargets = () => api.get<DailyTargets>('/profile/targets');
