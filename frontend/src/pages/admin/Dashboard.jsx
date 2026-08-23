import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import AdminNav from '../../components/AdminNav';
import { getCurrentAdmin } from '../../services/authService';
import { getDashboardMarcaciones } from '../../services/marcacionService';

const metricLabels = [
  ['trabajadores_activos', 'Trabajadores activos'],
  ['presentes_hoy', 'Presentes hoy'],
  ['entradas_registradas', 'Entradas registradas'],
  ['tardanzas', 'Tardanzas'],
  ['en_almuerzo', 'En almuerzo'],
  ['regresos_tardios', 'Regresos tardíos'],
  ['salidas', 'Salidas'],
  ['pendientes_salida', 'Pendientes de salida'],
];

export default function Dashboard() {
  const [admin, setAdmin] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getCurrentAdmin().then((response) => {
      setAdmin(response.data.admin);
    });
    getDashboardMarcaciones()
      .then((response) => setMetrics(response.data))
      .catch(() => setError('No se pudieron cargar los indicadores.'));
  }, []);

  return (
    <main className="admin-page">
      <section className="admin-shell">
        <header className="admin-header">
          <div>
            <p className="eyebrow">Panel administrativo</p>
            <h1>Administración</h1>
            <p className="muted">
              {admin
                ? `Sesión activa: ${admin.nombre} ${admin.apellido}`
                : 'Sesión activa.'}
            </p>
          </div>
        </header>
        <AdminNav />

        {error && <p className="error-message">{error}</p>}

        <section className="dashboard-grid">
          {metricLabels.map(([key, label]) => (
            <article className="metric-card" key={key}>
              <span>{label}</span>
              <strong>{metrics ? metrics[key] : '-'}</strong>
            </article>
          ))}
        </section>

        <section className="content-panel schedule-panel">
          <div className="button-row">
            <Link className="secondary-button link-button" to="/admin/trabajadores">
              Trabajadores
            </Link>
            <Link className="secondary-button link-button" to="/admin/horarios">
              Horarios
            </Link>
            <Link className="secondary-button link-button" to="/admin/marcaciones">
              Marcaciones
            </Link>
            <Link className="secondary-button link-button" to="/admin/reportes">
              Reportes
            </Link>
          </div>
        </section>
      </section>
    </main>
  );
}
