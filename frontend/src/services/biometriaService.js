/**
 * Modulo biometriaService de la interfaz del sistema de control de horarios.
 * Centraliza este flujo sin replicar decisiones de negocio del backend.
 */
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

/**

 * Registra la huella de un trabajador usando el template capturado por el agente cuando corresponde.

 *

 * @returns {Promise<unknown>|JSX.Element} Resultado de la operacion o elemento renderizado.

 */

export async function registrarHuella(trabajadorId, fingerprintId) {
  const payload = {};
  if (fingerprintId) {
    payload.fingerprint_id = fingerprintId;
  }

  if (useLocalAgent()) {
    const enrollment = await enrollFingerprintWithAgent();
    payload.template_biometrico = enrollment.data?.template_biometrico || enrollment.template_biometrico;
  }

  const response = await api.post(
    '/biometria/trabajadores/' + trabajadorId + '/registrar',
    payload,
    { timeout: 65000 },
  );
  return response.data;
}

/**

 * Solicita identificar una huella al endpoint biometrico en flujos sin agente local.

 *

 * @returns {Promise<unknown>|JSX.Element} Resultado de la operacion o elemento renderizado.

 */

export async function identificarHuella(fingerprintId) {
  const payload = {};
  if (fingerprintId) {
    payload.fingerprint_id = fingerprintId;
  }
  const response = await api.post('/biometria/identificar', payload, { timeout: 45000 });
  return response.data;
}
