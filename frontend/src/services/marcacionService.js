import api from './api';

export async function registrarMarcacionBiometrica() {
  const payload = {};
  const response = await api.post('/marcaciones/biometrica', payload, { timeout: 45000 });
  return response.data;
}

export async function listMarcacionesAdmin(params = {}) {
  const response = await api.get('/admin/marcaciones', { params });
  return response.data;
}

export async function getDashboardMarcaciones(params = {}) {
  const response = await api.get('/admin/marcaciones/dashboard', { params });
  return response.data;
}
