import api from './api';

export async function obtenerEstadoLector() {
  const response = await api.get('/biometria/device/status');
  return response.data;
}

export async function registrarHuella(trabajadorId, fingerprintId) {
  const payload = {};
  if (fingerprintId) {
    payload.fingerprint_id = fingerprintId;
  }
  const response = await api.post(
    `/biometria/trabajadores/${trabajadorId}/registrar`,
    payload,
    { timeout: 65000 },
  );
  return response.data;
}

export async function identificarHuella(fingerprintId) {
  const payload = {};
  if (fingerprintId) {
    payload.fingerprint_id = fingerprintId;
  }
  const response = await api.post('/biometria/identificar', payload, { timeout: 45000 });
  return response.data;
}
