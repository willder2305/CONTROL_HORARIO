/**
 * Modulo localAgentService de la interfaz del sistema de control de horarios.
 * Centraliza este flujo sin replicar decisiones de negocio del backend.
 */
import axios from 'axios';

function resolveAgentBaseUrl() {
  return import.meta.env.VITE_BIOMETRIC_AGENT_URL || 'http://127.0.0.1:8765';
}

/**

 * Indica si la interfaz debe usar ControlHorarioBiometricAgent en lugar de la API biometrica directa.

 *

 * @returns {Promise<unknown>|JSX.Element} Resultado de la operacion o elemento renderizado.

 */

export function useLocalAgent() {
  return import.meta.env.VITE_BIOMETRIC_MODE === 'local-agent';
}

const agentApi = axios.create({
  baseURL: resolveAgentBaseUrl(),
  timeout: 65000,
  withCredentials: false,
});

/**

 * Consulta /device/status del agente para mostrar disponibilidad real de SDK y ZK9500.

 *

 * @returns {Promise<unknown>|JSX.Element} Resultado de la operacion o elemento renderizado.

 */

export async function getAgentStatus() {
  const response = await agentApi.get('/device/status', { timeout: 12000 });
  return response.data;
}

/**

 * Solicita al agente la captura de tres muestras y devuelve el template temporal para registro autenticado.

 *

 * @returns {Promise<unknown>|JSX.Element} Resultado de la operacion o elemento renderizado.

 */

export async function enrollFingerprintWithAgent() {
  const response = await agentApi.post('/enroll', {}, { timeout: 90000 });
  return response.data;
}

/**

 * Solicita al agente identificar localmente y registrar en backend la siguiente marcacion automatica.

 *

 * @returns {Promise<unknown>|JSX.Element} Resultado de la operacion o elemento renderizado.

 */

export async function identifyAndMarkWithAgent() {
  const response = await agentApi.post('/identify-and-mark', {}, { timeout: 65000 });
  return response.data;
}
