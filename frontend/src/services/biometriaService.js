import api from './api';
import {
  enrollFingerprintWithAgent,
  getAgentStatus,
  useLocalAgent,
} from './localAgentService';

export async function obtenerEstadoLector() {
  if (useLocalAgent()) {
    const response = await getAgentStatus();
    return {
      success: response.success,
      data: {
        ...(response.data || {}),
        provider: 'local_agent',
        mode: 'local-agent',
      },
    };
  }

  const response = await api.get('/biometria/device/status');
  return response.data;
}

export async function registrarHuella(trabajadorId, fingerprintId, options = {}) {
  const payload = {};
  if (fingerprintId) {
    payload.fingerprint_id = fingerprintId;
  }

  if (useLocalAgent()) {
    const enrollment = await enrollFingerprintWithAgent({ onProgress: options.onProgress });
    payload.template_biometrico = enrollment.data?.template_biometrico || enrollment.template_biometrico;
  }

  const response = await api.post(
    '/biometria/trabajadores/' + trabajadorId + '/registrar',
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
