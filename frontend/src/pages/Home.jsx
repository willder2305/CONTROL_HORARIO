import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <main className="home-page">
      <section className="entry-panel" aria-labelledby="entry-title">
        <p className="eyebrow">Farmacia</p>
        <h1 id="entry-title">¿Cómo desea ingresar?</h1>
        <div className="entry-actions">
          <Link className="entry-button admin" to="/admin/login">
            Administrador
          </Link>
          <Link className="entry-button worker" to="/marcar">
            Trabajador
          </Link>
        </div>
      </section>
    </main>
  );
}
