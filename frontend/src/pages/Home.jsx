/**
 * Modulo de interfaz Home del sistema de control de horarios.
 * Mantiene la responsabilidad indicada sin duplicar logica de dominio del backend.
 */
import { Link } from 'react-router-dom';

/**
 * Muestra el punto de entrada público del sistema de control de horarios.
 *
 * Prioriza la marcación de asistencia y conserva el acceso administrativo
 * como un control discreto que puede utilizarse con teclado y lector de pantalla.
 *
 * @returns {JSX.Element} Pantalla inicial con acceso a marcación y administración.
 */
export default function Home() {
  return (
    <main className="home-page">
      <Link
        aria-label="Acceso administrador"
        className="admin-access-icon"
        title="Acceso administrador"
        to="/admin/login"
      >
        <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
          <path d="M12 12a4.25 4.25 0 1 0 0-8.5 4.25 4.25 0 0 0 0 8.5Zm0 2.25c-5 0-8.25 2.45-8.25 5.1 0 .64.51 1.15 1.15 1.15h14.2c.64 0 1.15-.51 1.15-1.15 0-2.65-3.25-5.1-8.25-5.1Z" />
        </svg>
      </Link>

      <section className="entry-panel home-entry-panel" aria-label="Control de horarios">
        <p className="eyebrow">Control de horarios</p>
        <Link className="entry-button worker home-mark-button" to="/marcar">
          Marcar
        </Link>
      </section>
    </main>
  );
}
