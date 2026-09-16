/**
 * Modulo de interfaz horarioService del sistema de control de horarios.
 * Mantiene la responsabilidad indicada sin duplicar logica de dominio del backend.
 */
import api from './api';

export async function listPlantillas() {
  const response = await api.get('/admin/horarios/plantillas');
  return response.data;
}

/**
 * Envia la operacion administrativa a la API y devuelve su respuesta para actualizar la interfaz.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export async function createPlantilla(payload) {
  const response = await api.post('/admin/horarios/plantillas', payload);
  return response.data;
}

/**
 * Envia la operacion administrativa a la API y devuelve su respuesta para actualizar la interfaz.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export async function updatePlantilla(id, payload) {
  const response = await api.put(`/admin/horarios/plantillas/${id}`, payload);
  return response.data;
}

/**
 * Envia la operacion administrativa a la API y devuelve su respuesta para actualizar la interfaz.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export async function desactivarPlantilla(id) {
  const response = await api.patch(`/admin/horarios/plantillas/${id}/desactivar`);
  return response.data;
}

/**
 * Envia la operacion administrativa a la API y devuelve su respuesta para actualizar la interfaz.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export async function asignarHorarioTrabajador(trabajadorId, payload) {
  const response = await api.post(
    `/admin/horarios/trabajadores/${trabajadorId}/asignar`,
    payload,
  );
  return response.data;
}

/**
 * Consulta la API correspondiente y devuelve los datos normalizados para la interfaz.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export async function getHistorialHorarios(trabajadorId) {
  const response = await api.get(
    `/admin/horarios/trabajadores/${trabajadorId}/historial`,
  );
  return response.data;
}
