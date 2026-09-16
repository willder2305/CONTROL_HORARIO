/**
 * Modulo de interfaz ProtectedRoute del sistema de control de horarios.
 * Mantiene la responsabilidad indicada sin duplicar logica de dominio del backend.
 */
import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';

import { getCurrentAdmin } from '../services/authService';
import Loading from './Loading';

/**
 * Restringe una ruta administrativa hasta verificar la sesion Flask vigente.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export default function ProtectedRoute({ children }) {
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    let active = true;

    getCurrentAdmin()
      .then(() => {
        if (active) setStatus('authenticated');
      })
      .catch(() => {
        if (active) setStatus('anonymous');
      });

    return () => {
      active = false;
    };
  }, []);

  if (status === 'loading') {
    return (
      <main className="page">
        <section className="content-panel">
          <Loading text="Validando sesión..." />
        </section>
      </main>
    );
  }

  if (status === 'anonymous') {
    return <Navigate to="/admin/login" replace />;
  }

  return children;
}
