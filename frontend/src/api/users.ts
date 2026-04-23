import api from './client';

export const exportAccountData = () =>
  api.get('/users/me/export', { responseType: 'blob' });

export const deleteAccount = () => api.delete('/users/me');
