/**
 * Modulo de interfaz reporteService del sistema de control de horarios.
 * Mantiene la responsabilidad indicada sin duplicar logica de dominio del backend.
 */
import api from './api';

export async function generarReportePantalla(params = {}) {
  const response = await api.get('/admin/reportes', { params });
  return response.data;
}

/**
 * Solicita la generacion o descarga del reporte respetando los filtros activos.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export async function descargarReporteExcel(params = {}) {
  const response = await api.get('/admin/reportes/excel', {
    params,
    responseType: 'blob',
  });
  return response.data;
}

/**
 * Solicita la generacion o descarga del reporte respetando los filtros activos.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export async function descargarReportePdf(params = {}) {
  const response = await api.get('/admin/reportes/pdf', {
    params,
    responseType: 'blob',
  });
  return response.data;
}
