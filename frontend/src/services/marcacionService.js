import api from './api';
import { identifyAndMarkWithAgent, useLocalAgent } from './localAgentService';

export async function registrarMarcacionBiometrica() {
  if (useLocalAgent()) {
    return identifyAndMarkWithAgent();
  }

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
