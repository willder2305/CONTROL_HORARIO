import { useEffect, useState } from 'react';

import AdminNav from '../../components/AdminNav';
import { listMarcacionesAdmin } from '../../services/marcacionService';
import { listTrabajadores } from '../../services/trabajadorService';

const initialFilters = {
  trabajador_id: '',
  tipo_marcacion: '',
  fecha: '',
  desde: '',
  hasta: '',
  estado: '',
  horario_id: '',
};

const markTypes = [
  ['ENTRADA', 'Entrada'],
  ['SALIDA_ALMUERZO', 'Salida almuerzo'],
  ['REGRESO_ALMUERZO', 'Regreso almuerzo'],
  ['SALIDA', 'Salida'],
];

const states = [
  ['A_TIEMPO', 'A tiempo'],
  ['TARDANZA', 'Tardanza'],
  ['ANTICIPADO', 'Anticipado'],
  ['SALIDA_ANTICIPADA', 'Salida anticipada'],
];

function MarkCell({ mark }) {
  if (!mark) return <span className="muted">-</span>;
  return (
    <span>
      {mark.hora}
      <small className="cell-note">{mark.estado}</small>
    </span>
  );
}

export default function Marcaciones() {
  const [filters, setFilters] = useState(initialFilters);
  const [workers, setWorkers] = useState([]);
  const [dayRows, setDayRows] = useState([]);
  const [marks, setMarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadData(params = filters) {
    setLoading(true);
    setError('');
    try {
      const [workersResponse, marksResponse] = await Promise.all([
        listTrabajadores(),
        listMarcacionesAdmin(params),
      ]);
      setWorkers(workersResponse.data.trabajadores);
      setDayRows(marksResponse.data.jornada);
      setMarks(marksResponse.data.marcaciones);
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ?? 'No se pudieron cargar marcaciones.',
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function handleChange(event) {
    setFilters((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  async function applyFilters(event) {
    event.preventDefault();
    await loadData(filters);
  }

  async function clearFilters() {
    setFilters(initialFilters);
    await loadData(initialFilters);
  }

  return (
    <main className="admin-page">
      <section className="admin-shell">
        <header className="admin-header">
          <div>
            <p className="eyebrow">Panel administrativo</p>
            <h1>Marcaciones</h1>
          </div>
        </header>
        <AdminNav />

        {error && <p className="error-message">{error}</p>}

        <section className="content-panel schedule-panel">
          <form className="mark-filters" onSubmit={applyFilters}>
            <label>
              Trabajador
              <select
                name="trabajador_id"
                value={filters.trabajador_id}
                onChange={handleChange}
              >
                <option value="">Todos</option>
                {workers.map((worker) => (
                  <option key={worker.id} value={worker.id}>
                    {worker.codigo} - {worker.nombre} {worker.apellido}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Tipo
              <select
                name="tipo_marcacion"
                value={filters.tipo_marcacion}
                onChange={handleChange}
              >
                <option value="">Todos</option>
                {markTypes.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Fecha
              <input
                type="date"
                name="fecha"
                value={filters.fecha}
                onChange={handleChange}
              />
            </label>
            <label>
              Desde
              <input
                type="date"
                name="desde"
                value={filters.desde}
                onChange={handleChange}
              />
            </label>
            <label>
              Hasta
              <input
                type="date"
                name="hasta"
                value={filters.hasta}
                onChange={handleChange}
              />
            </label>
            <label>
              Estado
              <select name="estado" value={filters.estado} onChange={handleChange}>
                <option value="">Todos</option>
                {states.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Horario
              <input
                type="number"
                min="1"
                name="horario_id"
                value={filters.horario_id}
                onChange={handleChange}
                placeholder="ID"
              />
            </label>
            <div className="button-row compact">
              <button className="plain-button" type="submit">
                Aplicar filtros
              </button>
              <button className="secondary-button" type="button" onClick={clearFilters}>
                Limpiar
              </button>
            </div>
          </form>
        </section>

        <section className="content-panel schedule-panel">
          <h2>Jornada</h2>
          {loading ? (
            <p className="muted">Cargando marcaciones...</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Trabajador</th>
                    <th>Entrada</th>
                    <th>Salida almuerzo</th>
                    <th>Regreso almuerzo</th>
                    <th>Salida</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {dayRows.map((row) => (
                    <tr key={`${row.fecha}-${row.trabajador_id}`}>
                      <td>{row.fecha}</td>
                      <td>
                        {row.codigo} - {row.trabajador}
                      </td>
                      <td><MarkCell mark={row.entrada} /></td>
                      <td><MarkCell mark={row.salida_almuerzo} /></td>
                      <td><MarkCell mark={row.regreso_almuerzo} /></td>
                      <td><MarkCell mark={row.salida} /></td>
                      <td>{row.estado}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!dayRows.length && <p className="muted">No hay marcaciones.</p>}
            </div>
          )}
        </section>

        <section className="content-panel schedule-panel">
          <h2>Detalle</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Código</th>
                  <th>Nombre</th>
                  <th>Tipo</th>
                  <th>Programada</th>
                  <th>Marcada</th>
                  <th>Estado</th>
                  <th>Diferencia</th>
                  <th>Horario</th>
                </tr>
              </thead>
              <tbody>
                {marks.map((mark) => (
                  <tr key={mark.id}>
                    <td>{mark.fecha}</td>
                    <td>{mark.codigo}</td>
                    <td>{mark.nombre} {mark.apellido}</td>
                    <td>{mark.tipo_marcacion}</td>
                    <td>{mark.hora_programada}</td>
                    <td>{mark.hora_real}</td>
                    <td>{mark.estado}</td>
                    <td>{mark.minutos_diferencia} min</td>
                    <td>{mark.horario_trabajador_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!marks.length && <p className="muted">No hay detalle para los filtros.</p>}
          </div>
        </section>
      </section>
    </main>
  );
}
