import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';

import { getCurrentAdmin } from '../services/authService';
import Loading from './Loading';

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
