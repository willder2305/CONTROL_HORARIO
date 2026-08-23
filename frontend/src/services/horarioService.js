import api from './api';

export async function listPlantillas() {
  const response = await api.get('/admin/horarios/plantillas');
  return response.data;
}

export async function createPlantilla(payload) {
  const response = await api.post('/admin/horarios/plantillas', payload);
  return response.data;
}

export async function updatePlantilla(id, payload) {
  const response = await api.put(`/admin/horarios/plantillas/${id}`, payload);
  return response.data;
}

export async function desactivarPlantilla(id) {
  const response = await api.patch(`/admin/horarios/plantillas/${id}/desactivar`);
  return response.data;
}

export async function asignarHorarioTrabajador(trabajadorId, payload) {
  const response = await api.post(
    `/admin/horarios/trabajadores/${trabajadorId}/asignar`,
    payload,
  );
  return response.data;
}

export async function getHistorialHorarios(trabajadorId) {
  const response = await api.get(
    `/admin/horarios/trabajadores/${trabajadorId}/historial`,
  );
  return response.data;
}
