import api from './api';

export async function login(usuario, password) {
  const response = await api.post('/auth/login', { usuario, password });
  return response.data;
}

export async function logout() {
  const response = await api.post('/auth/logout');
  return response.data;
}

export async function getCurrentAdmin() {
  const response = await api.get('/auth/me');
  return response.data;
}
