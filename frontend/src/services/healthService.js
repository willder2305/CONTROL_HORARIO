/**
 * Modulo de interfaz healthService del sistema de control de horarios.
 * Mantiene la responsabilidad indicada sin duplicar logica de dominio del backend.
 */
import api from './api';

export async function getHealth() {
  const response = await api.get('/health');
  return response.data;
}
