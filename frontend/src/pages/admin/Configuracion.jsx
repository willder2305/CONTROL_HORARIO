import AdminNav from '../../components/AdminNav';

export default function Configuracion() {
  return (
    <main className="admin-page">
      <section className="admin-shell">
        <header className="admin-header">
          <div>
            <p className="eyebrow">Panel administrativo</p>
            <h1>Configuración</h1>
          </div>
        </header>
        <AdminNav />

        <section className="content-panel schedule-panel">
          <h2>Parámetros operativos</h2>
          <dl className="settings-list">
            <div>
              <dt>Zona horaria</dt>
              <dd>America/Guatemala</dd>
            </div>
            <div>
              <dt>Biométrico</dt>
              <dd>Lector de huella ZK9500</dd>
            </div>
            <div>
              <dt>Base de datos</dt>
              <dd>Conectada</dd>
            </div>
          </dl>
        </section>
      </section>
    </main>
  );
}
