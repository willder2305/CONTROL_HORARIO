/**
 * Modulo de interfaz marcacionService del sistema de control de horarios.
 * Mantiene la responsabilidad indicada sin duplicar logica de dominio del backend.
 */
import api from './api';
import {
  getAgentHealth,
  getAgentStatus,
  identifyAndMarkWithAgent,
  useLocalAgent,
} from './localAgentService';

function agentError(code, message) {
  const error = new Error(message);
  error.response = { data: { code, message } };
  throw error;
}

export async function registrarMarcacionBiometrica() {
  if (useLocalAgent()) {
    const health = await getAgentHealth();
    if (!health?.success) {
      agentError('AGENT_OFFLINE', 'Servicio biometrico no disponible.');
    }

    const status = await getAgentStatus();
    if (!status?.data?.ready) {
      agentError('LECTOR_NO_DETECTADO', 'Lector ZKTeco ZK9500 no detectado.');
    }

    return identifyAndMarkWithAgent();
  }

  const payload = {};
  const response = await api.post('/marcaciones/biometrica', payload, { timeout: 45000 });
  return response.data;
}

/**
 * Consulta la API correspondiente y devuelve los datos normalizados para la interfaz.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export async function listMarcacionesAdmin(params = {}) {
  const response = await api.get('/admin/marcaciones', { params });
  return response.data;
}

/**
 * Consulta la API correspondiente y devuelve los datos normalizados para la interfaz.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export async function getDashboardMarcaciones(params = {}) {
  const response = await api.get('/admin/marcaciones/dashboard', { params });
  return response.data;
}
