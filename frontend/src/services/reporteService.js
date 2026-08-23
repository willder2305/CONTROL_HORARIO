import api from './api';

export async function generarReportePantalla(params = {}) {
  const response = await api.get('/admin/reportes', { params });
  return response.data;
}

export async function descargarReporteExcel(params = {}) {
  const response = await api.get('/admin/reportes/excel', {
    params,
    responseType: 'blob',
  });
  return response.data;
}

export async function descargarReportePdf(params = {}) {
  const response = await api.get('/admin/reportes/pdf', {
    params,
    responseType: 'blob',
  });
  return response.data;
}
