import { useEffect, useMemo, useState } from 'react';

import AdminNav from '../../components/AdminNav';
import {
  asignarHorarioTrabajador,
  createPlantilla,
  desactivarPlantilla,
  getHistorialHorarios,
  listPlantillas,
  updatePlantilla,
} from '../../services/horarioService';
import { listTrabajadores } from '../../services/trabajadorService';

const templateFormInitial = {
  id: null,
  nombre: '',
  hora_entrada: '08:00',
  hora_salida_almuerzo: '12:45',
  hora_regreso_almuerzo: '13:45',
  hora_salida: '18:00',
  tolerancia_entrada: 0,
  tolerancia_regreso_almuerzo: 0,
};

const assignmentInitial = {
  trabajador_id: '',
  modo: 'plantilla',
  plantilla_id: '',
  fecha_inicio: new Date().toISOString().slice(0, 10),
  hora_entrada: '08:00',
  hora_salida_almuerzo: '12:45',
  hora_regreso_almuerzo: '13:45',
  hora_salida: '18:00',
  tolerancia_entrada: 0,
  tolerancia_regreso_almuerzo: 0,
};

export default function Horarios() {
  const [plantillas, setPlantillas] = useState([]);
  const [trabajadores, setTrabajadores] = useState([]);
  const [historial, setHistorial] = useState([]);
  const [templateForm, setTemplateForm] = useState(templateFormInitial);
  const [assignment, setAssignment] = useState(assignmentInitial);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const isEditingTemplate = useMemo(() => Boolean(templateForm.id), [templateForm.id]);

  async function loadData(selectedWorkerId = assignment.trabajador_id) {
    const [templatesResponse, workersResponse] = await Promise.all([
      listPlantillas(),
      listTrabajadores({ estado: 'activo' }),
    ]);
    setPlantillas(templatesResponse.data.plantillas);
    setTrabajadores(workersResponse.data.trabajadores);

    if (selectedWorkerId) {
      const historyResponse = await getHistorialHorarios(selectedWorkerId);
      setHistorial(historyResponse.data.historial);
    } else {
      setHistorial([]);
    }
  }

  useEffect(() => {
    loadData().catch(() => setError('No se pudieron cargar los horarios.'));
  }, []);

  function handleTemplateChange(event) {
    setTemplateForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  function handleAssignmentChange(event) {
    const nextValue = event.target.value;
    setAssignment((current) => ({
      ...current,
      [event.target.name]: nextValue,
    }));

    if (event.target.name === 'trabajador_id' && nextValue) {
      getHistorialHorarios(nextValue)
        .then((response) => setHistorial(response.data.historial))
        .catch(() => setHistorial([]));
    }
  }

  async function saveTemplate(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    try {
      const response = isEditingTemplate
        ? await updatePlantilla(templateForm.id, templateForm)
        : await createPlantilla(templateForm);
      setMessage(response.message);
      setTemplateForm(templateFormInitial);
      await loadData();
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ??
          'No se pudo guardar la plantilla de horario.',
      );
    }
  }

  function editTemplate(template) {
    setTemplateForm({
      ...template,
      hora_salida_almuerzo: template.hora_salida_almuerzo ?? '',
      hora_regreso_almuerzo: template.hora_regreso_almuerzo ?? '',
    });
    setError('');
    setMessage('');
  }

  async function disableTemplate(template) {
    setError('');
    setMessage('');
    try {
      const response = await desactivarPlantilla(template.id);
      setMessage(response.message);
      await loadData();
    } catch (requestError) {
      setError(requestError.response?.data?.message ?? 'No se pudo desactivar.');
    }
  }

  async function assignSchedule(event) {
    event.preventDefault();
    setError('');
    setMessage('');

    const payload =
      assignment.modo === 'plantilla'
        ? {
            plantilla_id: assignment.plantilla_id,
            fecha_inicio: assignment.fecha_inicio,
          }
        : {
            fecha_inicio: assignment.fecha_inicio,
            hora_entrada: assignment.hora_entrada,
            hora_salida_almuerzo: assignment.hora_salida_almuerzo,
            hora_regreso_almuerzo: assignment.hora_regreso_almuerzo,
            hora_salida: assignment.hora_salida,
            tolerancia_entrada: assignment.tolerancia_entrada,
            tolerancia_regreso_almuerzo: assignment.tolerancia_regreso_almuerzo,
          };

    try {
      const response = await asignarHorarioTrabajador(
        assignment.trabajador_id,
        payload,
      );
      setMessage(response.message);
      await loadData(assignment.trabajador_id);
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ??
          'No se pudo asignar el horario al trabajador.',
      );
    }
  }

  return (
    <main className="admin-page">
      <section className="admin-shell">
        <header className="admin-header">
          <div>
            <p className="eyebrow">Panel administrativo</p>
            <h1>Horarios</h1>
          </div>
        </header>
        <AdminNav />

        {error && <p className="error-message">{error}</p>}
        {message && <p className="success-message">{message}</p>}

        <section className="admin-grid">
          <form className="content-panel worker-form" onSubmit={saveTemplate}>
            <h2>{isEditingTemplate ? 'Editar plantilla' : 'Crear plantilla'}</h2>
            <label>
              Nombre
              <input
                type="text"
                name="nombre"
                value={templateForm.nombre}
                onChange={handleTemplateChange}
                required
              />
            </label>
            <div className="form-grid">
              <label>
                Entrada
                <input
                  type="time"
                  name="hora_entrada"
                  value={templateForm.hora_entrada}
                  onChange={handleTemplateChange}
                  required
                />
              </label>
              <label>
                Salida almuerzo
                <input
                  type="time"
                  name="hora_salida_almuerzo"
                  value={templateForm.hora_salida_almuerzo}
                  onChange={handleTemplateChange}
                />
              </label>
              <label>
                Regreso almuerzo
                <input
                  type="time"
                  name="hora_regreso_almuerzo"
                  value={templateForm.hora_regreso_almuerzo}
                  onChange={handleTemplateChange}
                />
              </label>
              <label>
                Salida
                <input
                  type="time"
                  name="hora_salida"
                  value={templateForm.hora_salida}
                  onChange={handleTemplateChange}
                  required
                />
              </label>
              <label>
                Tolerancia entrada
                <input
                  type="number"
                  min="0"
                  name="tolerancia_entrada"
                  value={templateForm.tolerancia_entrada}
                  onChange={handleTemplateChange}
                />
              </label>
              <label>
                Tolerancia regreso
                <input
                  type="number"
                  min="0"
                  name="tolerancia_regreso_almuerzo"
                  value={templateForm.tolerancia_regreso_almuerzo}
                  onChange={handleTemplateChange}
                />
              </label>
            </div>
            <div className="button-row">
              <button className="plain-button" type="submit">
                {isEditingTemplate ? 'Guardar plantilla' : 'Crear plantilla'}
              </button>
              {isEditingTemplate && (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => setTemplateForm(templateFormInitial)}
                >
                  Cancelar
                </button>
              )}
            </div>
          </form>

          <section className="content-panel worker-list">
            <h2>Plantillas</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Nombre</th>
                    <th>Entrada</th>
                    <th>Almuerzo</th>
                    <th>Regreso</th>
                    <th>Salida</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {plantillas.map((template) => (
                    <tr key={template.id}>
                      <td>{template.nombre}</td>
                      <td>{template.hora_entrada}</td>
                      <td>{template.hora_salida_almuerzo ?? 'Sin almuerzo'}</td>
                      <td>{template.hora_regreso_almuerzo ?? 'Sin almuerzo'}</td>
                      <td>{template.hora_salida}</td>
                      <td>
                        <span className={template.activo ? 'status active' : 'status inactive'}>
                          {template.activo ? 'Activa' : 'Inactiva'}
                        </span>
                      </td>
                      <td>
                        <div className="table-actions">
                          <button
                            className="secondary-button"
                            type="button"
                            onClick={() => editTemplate(template)}
                          >
                            Editar
                          </button>
                          {template.activo && (
                            <button
                              className="secondary-button"
                              type="button"
                              onClick={() => disableTemplate(template)}
                            >
                              Desactivar
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </section>

        <section className="content-panel schedule-panel">
          <h2>Asignar horario a trabajador</h2>
          <form className="assignment-form" onSubmit={assignSchedule}>
            <label>
              Trabajador
              <select
                name="trabajador_id"
                value={assignment.trabajador_id}
                onChange={handleAssignmentChange}
                required
              >
                <option value="">Seleccione</option>
                {trabajadores.map((worker) => (
                  <option key={worker.id} value={worker.id}>
                    {worker.codigo} - {worker.nombre} {worker.apellido}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Modo
              <select name="modo" value={assignment.modo} onChange={handleAssignmentChange}>
                <option value="plantilla">Usar plantilla</option>
                <option value="personalizado">Horario personalizado</option>
              </select>
            </label>
            <label>
              Fecha inicio
              <input
                type="date"
                name="fecha_inicio"
                value={assignment.fecha_inicio}
                onChange={handleAssignmentChange}
                required
              />
            </label>
            {assignment.modo === 'plantilla' ? (
              <label>
                Plantilla
                <select
                  name="plantilla_id"
                  value={assignment.plantilla_id}
                  onChange={handleAssignmentChange}
                  required
                >
                  <option value="">Seleccione</option>
                  {plantillas
                    .filter((template) => template.activo)
                    .map((template) => (
                      <option key={template.id} value={template.id}>
                        {template.nombre}
                      </option>
                    ))}
                </select>
              </label>
            ) : (
              <div className="form-grid full-row">
                <label>
                  Entrada
                  <input
                    type="time"
                    name="hora_entrada"
                    value={assignment.hora_entrada}
                    onChange={handleAssignmentChange}
                    required
                  />
                </label>
                <label>
                  Salida almuerzo
                    <input
                      type="time"
                      name="hora_salida_almuerzo"
                      value={assignment.hora_salida_almuerzo}
                      onChange={handleAssignmentChange}
                    />
                </label>
                <label>
                  Regreso almuerzo
                    <input
                      type="time"
                      name="hora_regreso_almuerzo"
                      value={assignment.hora_regreso_almuerzo}
                      onChange={handleAssignmentChange}
                    />
                </label>
                <label>
                  Salida
                  <input
                    type="time"
                    name="hora_salida"
                    value={assignment.hora_salida}
                    onChange={handleAssignmentChange}
                    required
                  />
                </label>
                <label>
                  Tolerancia entrada
                  <input
                    type="number"
                    min="0"
                    name="tolerancia_entrada"
                    value={assignment.tolerancia_entrada}
                    onChange={handleAssignmentChange}
                  />
                </label>
                <label>
                  Tolerancia regreso
                  <input
                    type="number"
                    min="0"
                    name="tolerancia_regreso_almuerzo"
                    value={assignment.tolerancia_regreso_almuerzo}
                    onChange={handleAssignmentChange}
                  />
                </label>
              </div>
            )}
            <button className="plain-button" type="submit">
              Asignar horario
            </button>
          </form>
        </section>

        <section className="content-panel schedule-panel">
          <h2>Historial de horarios</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Inicio</th>
                  <th>Fin</th>
                  <th>Plantilla</th>
                  <th>Entrada</th>
                  <th>Almuerzo</th>
                  <th>Regreso</th>
                  <th>Salida</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {historial.map((schedule) => (
                  <tr key={schedule.id}>
                    <td>{schedule.fecha_inicio}</td>
                    <td>{schedule.fecha_fin ?? 'Vigente'}</td>
                    <td>{schedule.plantilla_nombre ?? 'Personalizado'}</td>
                    <td>{schedule.hora_entrada}</td>
                    <td>{schedule.hora_salida_almuerzo ?? 'Sin almuerzo'}</td>
                    <td>{schedule.hora_regreso_almuerzo ?? 'Sin almuerzo'}</td>
                    <td>{schedule.hora_salida}</td>
                    <td>
                      <span className={schedule.activo ? 'status active' : 'status inactive'}>
                        {schedule.activo ? 'Activo' : 'Histórico'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!historial.length && <p className="muted">Seleccione un trabajador.</p>}
          </div>
        </section>
      </section>
    </main>
  );
}
