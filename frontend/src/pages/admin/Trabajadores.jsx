import { useEffect, useMemo, useState } from 'react';

import AdminNav from '../../components/AdminNav';
import { obtenerEstadoLector, registrarHuella } from '../../services/biometriaService';
import {
  activarTrabajador,
  createTrabajador,
  desactivarTrabajador,
  listTrabajadores,
  updateTrabajador,
} from '../../services/trabajadorService';

const initialForm = {
  id: null,
  codigo: '',
  nombre: '',
  apellido: '',
  fingerprintId: '',
};

export default function Trabajadores() {
  const [trabajadores, setTrabajadores] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [filters, setFilters] = useState({ q: '', estado: '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [readerStatus, setReaderStatus] = useState(null);
  const [fingerprintModal, setFingerprintModal] = useState(null);
  const isEditing = useMemo(() => Boolean(form.id), [form.id]);
  const isMockMode = readerStatus?.provider === 'mock';
  const isPhysicalReader = ['zk9500', 'local_agent'].includes(readerStatus?.provider);

  function updateFingerprintProgress(body) {
    setFingerprintModal((current) => (current ? { ...current, body } : current));
  }

  async function loadWorkers(params = filters) {
    setLoading(true);
    setError('');
    try {
      const response = await listTrabajadores(params);
      setTrabajadores(response.data.trabajadores);
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ?? 'No se pudieron cargar trabajadores.',
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadReaderStatus() {
    try {
      const response = await obtenerEstadoLector();
      setReaderStatus(response.data);
    } catch {
      setReaderStatus(null);
    }
  }

  useEffect(() => {
    loadWorkers();
    loadReaderStatus();
  }, []);

  function handleFormChange(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  function handleFilterChange(event) {
    setFilters((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setMessage('');

    const payload = {
      codigo: form.codigo.trim(),
      nombre: form.nombre.trim(),
      apellido: form.apellido.trim(),
    };

    if (!isEditing) {
      payload.enroll_fingerprint = true;
      if (form.fingerprintId.trim()) {
        payload.fingerprint_id = form.fingerprintId.trim();
      }
      setFingerprintModal({
        title: 'Registrar huella',
        body: isMockMode ? 'Validando huella de desarrollo...' : 'Comprobando lector...',
      });
    }

    try {
      const response = isEditing
        ? await updateTrabajador(form.id, payload)
        : await createTrabajador(payload, { onProgress: updateFingerprintProgress });
      setMessage(response.message);
      setForm(initialForm);
      await loadWorkers();
      await loadReaderStatus();
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ??
          requestError.response?.data?.errors?.nombre ??
          'No se pudo guardar el trabajador.',
      );
    } finally {
      setFingerprintModal(null);
    }
  }

  function editWorker(worker) {
    setForm({
      id: worker.id,
      codigo: worker.codigo,
      nombre: worker.nombre,
      apellido: worker.apellido,
      fingerprintId: '',
    });
    setMessage('');
    setError('');
  }

  async function toggleWorker(worker) {
    setError('');
    setMessage('');
    try {
      const response = worker.activo
        ? await desactivarTrabajador(worker.id)
        : await activarTrabajador(worker.id);
      setMessage(response.message);
      await loadWorkers();
    } catch (requestError) {
      setError(requestError.response?.data?.message ?? 'No se pudo cambiar el estado.');
    }
  }

  async function registerFingerprint(worker) {
    const fingerprintId = isMockMode
      ? window.prompt(`Identificacion biometrica de desarrollo para ${worker.codigo}.`, '')
      : '';

    if (fingerprintId === null) return;

    setError('');
    setMessage('');
    setFingerprintModal({
      title: 'Registrar huella',
      body: isMockMode ? 'Validando huella de desarrollo...' : 'Comprobando lector...',
    });

    try {
      const response = await registrarHuella(worker.id, fingerprintId, { onProgress: updateFingerprintProgress });
      setMessage(response.message);
      await loadWorkers();
      await loadReaderStatus();
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ?? 'No se pudo registrar la huella.',
      );
    } finally {
      setFingerprintModal(null);
    }
  }

  async function applyFilters(event) {
    event.preventDefault();
    await loadWorkers(filters);
  }

  async function clearFilters() {
    const emptyFilters = { q: '', estado: '' };
    setFilters(emptyFilters);
    await loadWorkers(emptyFilters);
  }

  return (
    <main className="admin-page">
      <section className="admin-shell">
        <header className="admin-header">
          <div>
            <p className="eyebrow">Panel administrativo</p>
            <h1>Trabajadores</h1>
          </div>
        </header>
        <AdminNav />

        <section className="admin-grid">
          <form className="content-panel worker-form" onSubmit={handleSubmit}>
            <h2>{isEditing ? 'Editar trabajador' : 'Crear trabajador'}</h2>
            <label>
              Codigo
              <input
                type="text"
                name="codigo"
                placeholder="Automatico"
                value={form.codigo}
                onChange={handleFormChange}
              />
            </label>
            <label>
              Nombre
              <input
                type="text"
                name="nombre"
                value={form.nombre}
                onChange={handleFormChange}
                required
              />
            </label>
            <label>
              Apellido
              <input
                type="text"
                name="apellido"
                value={form.apellido}
                onChange={handleFormChange}
                required
              />
            </label>

            {!isEditing && (
              <section className="fingerprint-required-panel">
                <h3>Huella digital</h3>
                <p className="muted">
                  Huella no registrada. Para crear un trabajador activo debe registrar una huella.
                </p>
                <p className="muted">
                  Lector: {isPhysicalReader ? 'ZKTeco ZK9500' : 'Modo desarrollo'}
                </p>
                {isMockMode && (
                  <label>
                    Huella de desarrollo
                    <input
                      type="text"
                      name="fingerprintId"
                      value={form.fingerprintId}
                      onChange={handleFormChange}
                      placeholder="FP0001"
                      required
                    />
                  </label>
                )}
              </section>
            )}

            {error && <p className="error-message">{error}</p>}
            {message && <p className="success-message">{message}</p>}
            <div className="button-row">
              <button className="plain-button" type="submit">
                {isEditing ? 'Guardar cambios' : 'Registrar huella y crear trabajador'}
              </button>
              {isEditing && (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => setForm(initialForm)}
                >
                  Cancelar
                </button>
              )}
            </div>
          </form>

          <section className="content-panel worker-list">
            <form className="filters" onSubmit={applyFilters}>
              <label>
                Buscar
                <input
                  type="search"
                  name="q"
                  value={filters.q}
                  onChange={handleFilterChange}
                  placeholder="Codigo, nombre o apellido"
                />
              </label>
              <label>
                Estado
                <select name="estado" value={filters.estado} onChange={handleFilterChange}>
                  <option value="">Todos</option>
                  <option value="activo">Activos</option>
                  <option value="inactivo">Inactivos</option>
                </select>
              </label>
              <div className="button-row compact">
                <button className="plain-button" type="submit">
                  Filtrar
                </button>
                <button className="secondary-button" type="button" onClick={clearFilters}>
                  Limpiar
                </button>
              </div>
            </form>

            {loading ? (
              <p className="muted">Cargando trabajadores...</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Codigo</th>
                      <th>Nombre</th>
                      <th>Apellido</th>
                      <th>Estado</th>
                      <th>Horario</th>
                      <th>Huella</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trabajadores.map((worker) => (
                      <tr key={worker.id}>
                        <td>{worker.codigo}</td>
                        <td>{worker.nombre}</td>
                        <td>{worker.apellido}</td>
                        <td>
                          <span className={worker.activo ? 'status active' : 'status inactive'}>
                            {worker.estado}
                          </span>
                        </td>
                        <td>
                          {worker.horario
                            ? `${worker.horario.hora_entrada} - ${worker.horario.hora_salida}`
                            : 'Sin asignar'}
                        </td>
                        <td>{worker.estado_huella}</td>
                        <td>
                          <div className="table-actions">
                            <button
                              className="secondary-button"
                              type="button"
                              onClick={() => editWorker(worker)}
                            >
                              Editar
                            </button>
                            <button
                              className="secondary-button"
                              type="button"
                              onClick={() => toggleWorker(worker)}
                            >
                              {worker.activo ? 'Desactivar' : 'Activar'}
                            </button>
                            <button
                              className="secondary-button"
                              type="button"
                              onClick={() => registerFingerprint(worker)}
                            >
                              Registrar huella
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!trabajadores.length && <p className="muted">No hay trabajadores.</p>}
              </div>
            )}
          </section>
        </section>

        {fingerprintModal && (
          <div className="modal-backdrop" role="status" aria-live="polite">
            <section className="modal-panel">
              <h2>{fingerprintModal.title}</h2>
              <p className="reader-title">ZKTeco ZK9500</p>
              {fingerprintModal.body.includes('conectado') && (
                <p className="success-message">Lector conectado</p>
              )}
              <p>{fingerprintModal.body}</p>
              <p className="muted">Capturas requeridas: 1 de 3, 2 de 3 y 3 de 3.</p>
              <p className="muted">Retire el dedo entre cada captura.</p>
            </section>
          </div>
        )}
      </section>
    </main>
  );
}
