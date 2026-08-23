import api from './api';
import { enrollFingerprintWithAgent, useLocalAgent } from './localAgentService';

export async function listTrabajadores(params = {}) {
  const response = await api.get('/admin/trabajadores', { params });
  return response.data;
}

export async function createTrabajador(payload) {
  const requestPayload = { ...payload };

  if (useLocalAgent() && requestPayload.enroll_fingerprint && !requestPayload.template_biometrico) {
    const enrollment = await enrollFingerprintWithAgent();
    requestPayload.template_biometrico = enrollment.data?.template_biometrico || enrollment.template_biometrico;
  }

  const response = await api.post('/admin/trabajadores', requestPayload, {
    timeout: requestPayload.enroll_fingerprint ? 65000 : 10000,
  });
  return response.data;
}

export async function updateTrabajador(id, payload) {
  const response = await api.put('/admin/trabajadores/' + id, payload);
  return response.data;
}

export async function activarTrabajador(id) {
  const response = await api.patch('/admin/trabajadores/' + id + '/activar');
  return response.data;
}

export async function desactivarTrabajador(id) {
  const response = await api.patch('/admin/trabajadores/' + id + '/desactivar');
  return response.data;
}
