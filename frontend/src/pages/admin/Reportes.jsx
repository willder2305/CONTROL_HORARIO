import { useEffect, useState } from 'react';

import AdminNav from '../../components/AdminNav';
import {
  descargarReporteExcel,
  descargarReportePdf,
  generarReportePantalla,
} from '../../services/reporteService';
import { listTrabajadores } from '../../services/trabajadorService';

const initialFilters = {
  trabajador_id: '',
  tipo_marcacion: '',
  estado: '',
  fecha: '',
  desde: '',
  hasta: '',
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

const summaryLabels = [
  ['total_marcaciones', 'Total marcaciones'],
  ['total_tardanzas', 'Tardanzas'],
  ['total_a_tiempo', 'A tiempo'],
  ['total_salidas_anticipadas', 'Salidas anticipadas'],
  ['total_anticipados', 'Anticipados'],
  ['trabajadores_incluidos', 'Trabajadores'],
];

export default function Reportes() {
  const [filters, setFilters] = useState(initialFilters);
  const [workers, setWorkers] = useState([]);
  const [summary, setSummary] = useState(null);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function loadReport(params = filters) {
    setLoading(true);
    setError('');
    try {
      const [workersResponse, reportResponse] = await Promise.all([
        listTrabajadores(),
        generarReportePantalla(params),
      ]);
      setWorkers(workersResponse.data.trabajadores);
      setSummary(reportResponse.data.resumen);
      setResults(reportResponse.data.resultados);
    } catch (requestError) {
      setError(requestError.response?.data?.message ?? 'No se pudo generar el reporte.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReport();
  }, []);

  function handleChange(event) {
    setFilters((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  async function applyFilters(event) {
    event.preventDefault();
    await loadReport(filters);
  }

  async function clearFilters() {
    setFilters(initialFilters);
    await loadReport(initialFilters);
  }

  async function downloadExcel() {
    setError('');
    try {
      const blob = await descargarReporteExcel(filters);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'reporte_control_horarios.xlsx';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(requestError.response?.data?.message ?? 'No se pudo descargar el Excel.');
    }
  }

  async function downloadPdf() {
    setError('');
    try {
      const blob = await descargarReportePdf(filters);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'reporte_control_horarios.pdf';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(requestError.response?.data?.message ?? 'No se pudo descargar el PDF.');
    }
  }

  return (
    <main className="admin-page">
      <section className="admin-shell">
        <header className="admin-header">
          <div>
            <p className="eyebrow">Panel administrativo</p>
            <h1>Reportes</h1>
          </div>
        </header>
        <AdminNav />

        {error && <p className="error-message">{error}</p>}

        <section className="content-panel schedule-panel">
          <form className="mark-filters" onSubmit={applyFilters}>
            <label>
              Trabajador
              <select name="trabajador_id" value={filters.trabajador_id} onChange={handleChange}>
                <option value="">Todos</option>
                {workers.map((worker) => (
                  <option key={worker.id} value={worker.id}>
                    {worker.codigo} - {worker.nombre} {worker.apellido}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Tipo marcación
              <select name="tipo_marcacion" value={filters.tipo_marcacion} onChange={handleChange}>
                <option value="">Todos</option>
                {markTypes.map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </label>
            <label>
              Estado
              <select name="estado" value={filters.estado} onChange={handleChange}>
                <option value="">Todos</option>
                {states.map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </label>
            <label>
              Fecha
              <input type="date" name="fecha" value={filters.fecha} onChange={handleChange} />
            </label>
            <label>
              Desde
              <input type="date" name="desde" value={filters.desde} onChange={handleChange} />
            </label>
            <label>
              Hasta
              <input type="date" name="hasta" value={filters.hasta} onChange={handleChange} />
            </label>
            <div className="button-row compact">
              <button className="plain-button" type="submit">Generar</button>
              <button className="secondary-button" type="button" onClick={downloadExcel}>Descargar Excel</button>
              <button className="secondary-button" type="button" onClick={downloadPdf}>Descargar PDF</button>
              <button className="secondary-button" type="button" onClick={clearFilters}>Limpiar</button>
            </div>
          </form>
        </section>

        <section className="dashboard-grid schedule-panel">
          {summaryLabels.map(([key, label]) => (
            <article className="metric-card" key={key}>
              <span>{label}</span>
              <strong>{summary ? summary[key] : '-'}</strong>
            </article>
          ))}
        </section>

        <section className="content-panel schedule-panel">
          <h2>Resultados</h2>
          {loading ? (
            <p className="muted">Generando reporte...</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Código</th>
                    <th>Trabajador</th>
                    <th>Tipo</th>
                    <th>Programada</th>
                    <th>Marcada</th>
                    <th>Estado</th>
                    <th>Diferencia</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((mark) => (
                    <tr key={mark.id}>
                      <td>{mark.fecha}</td>
                      <td>{mark.codigo}</td>
                      <td>{mark.nombre} {mark.apellido}</td>
                      <td>{mark.tipo_marcacion}</td>
                      <td>{mark.hora_programada}</td>
                      <td>{mark.hora_real}</td>
                      <td>{mark.estado}</td>
                      <td>{mark.minutos_diferencia} min</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!results.length && <p className="muted">No hay resultados.</p>}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
