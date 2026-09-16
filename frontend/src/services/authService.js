/**
 * Modulo de interfaz authService del sistema de control de horarios.
 * Mantiene la responsabilidad indicada sin duplicar logica de dominio del backend.
 */
import api from './api';

export async function login(usuario, password) {
  const response = await api.post('/auth/login', { usuario, password });
  return response.data;
}

/**
 * Cierra la sesion Flask y devuelve la confirmacion de la API. authService.js.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export async function logout() {
  const response = await api.post('/auth/logout');
  return response.data;
}

/**
 * Consulta la API correspondiente y devuelve los datos normalizados para la interfaz.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export async function getCurrentAdmin() {
  const response = await api.get('/auth/me');
  return response.data;
}
