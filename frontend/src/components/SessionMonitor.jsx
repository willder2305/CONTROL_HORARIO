import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { getSessionStatus, logout, refreshSession } from '../services/authService';

const WARNING_SECONDS = 120;

function formatRemaining(seconds) {
  const minutes = Math.max(1, Math.ceil(seconds / 60));
  return `${minutes} minuto${minutes === 1 ? '' : 's'}`;
}

export default function SessionMonitor() {
  const navigate = useNavigate();
  const [secondsRemaining, setSecondsRemaining] = useState(null);
  const [expired, setExpired] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    let active = true;

    async function checkSession() {
      try {
        const response = await getSessionStatus();
        if (active) setSecondsRemaining(response.data.seconds_remaining);
      } catch (error) {
        if (error.response?.status === 401 && active) setExpired(true);
      }
    }

    function markExpired() {
      if (active) setExpired(true);
    }

    checkSession();
    const intervalId = window.setInterval(checkSession, 30000);
    window.addEventListener('auth:expired', markExpired);
    return () => {
      active = false;
      window.clearInterval(intervalId);
      window.removeEventListener('auth:expired', markExpired);
    };
  }, []);

  useEffect(() => {
    if (!expired) return undefined;
    sessionStorage.removeItem('csrfToken');
    const timeoutId = window.setTimeout(() => navigate('/admin/login', { replace: true }), 4000);
    return () => window.clearTimeout(timeoutId);
  }, [expired, navigate]);

  async function continueSession() {
    setRefreshing(true);
    try {
      const response = await refreshSession();
      setSecondsRemaining(response.data.seconds_remaining);
    } catch (error) {
      if (error.response?.status === 401) setExpired(true);
    } finally {
      setRefreshing(false);
    }
  }

  async function closeSession() {
    try {
      await logout();
    } finally {
      sessionStorage.removeItem('csrfToken');
      navigate('/admin/login', { replace: true });
    }
  }

  if (expired) {
    return (
      <div className="modal-backdrop" role="alertdialog" aria-modal="true" aria-labelledby="session-expired-title">
        <section className="modal-panel">
          <h2 id="session-expired-title">Su sesión ha expirado</h2>
          <p>Por seguridad debe iniciar sesión nuevamente.</p>
          <button className="plain-button" type="button" onClick={() => navigate('/admin/login', { replace: true })}>
            Ir al inicio de sesión
          </button>
        </section>
      </div>
    );
  }

  if (secondsRemaining === null || secondsRemaining > WARNING_SECONDS) return null;

  return (
    <section className="session-warning" role="alert" aria-live="polite">
      <div>
        <strong>Su sesión está por finalizar.</strong>
        <span>La sesión expirará en {formatRemaining(secondsRemaining)}.</span>
      </div>
      <div className="button-row compact">
        <button className="plain-button" type="button" disabled={refreshing} onClick={continueSession}>
          {refreshing ? 'Continuando...' : 'Continuar sesión'}
        </button>
        <button className="secondary-button" type="button" onClick={closeSession}>
          Cerrar sesión
        </button>
      </div>
    </section>
  );
}
