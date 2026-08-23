import { useState } from 'react';
import { Link } from 'react-router-dom';

import { registrarMarcacionBiometrica } from '../services/marcacionService';

function friendlyError(requestError) {
  const code = requestError.response?.data?.code;
  if (code === 'HUELLA_NO_RECONOCIDA') {
    return 'Huella no reconocida. La huella no se encuentra registrada.';
  }
  if (code === 'LECTOR_NO_DISPONIBLE') {
    return 'Lector de huellas no disponible. Verifique la conexión del ZKTeco ZK9500.';
  }
  if (code === 'HORARIO_NO_ASIGNADO') {
    return 'No se puede realizar la marcación. No tiene un horario asignado para esta jornada.';
  }
  if (code === 'TRABAJADOR_INACTIVO') {
    return 'No se puede realizar la marcación. Consulte con el administrador.';
  }
  if (code === 'JORNADA_COMPLETADA') {
    return 'Jornada completada. Ya se registraron todas las marcaciones de esta jornada.';
  }
  if (code === 'MARCACION_RECIENTE') {
    return 'La marcación ya se está procesando. Intente nuevamente en unos segundos.';
  }
  if (requestError.code === 'ECONNABORTED') {
    return 'No se detectó ninguna huella. Intente nuevamente.';
  }
  return requestError.response?.data?.message ?? 'No se pudo realizar la marcación.';
}

export default function Marcar() {
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  async function markAttendance() {
    setError('');
    setResult(null);
    setStatus('reading');

    try {
      const response = await registrarMarcacionBiometrica();
      const data = response.data;
      const mark = data.marcacion;
      setResult({
        tipo: data.tipoMarcacionTexto ?? mark.tipoMarcacionTexto,
        hora: data.horaRegistrada ?? mark.horaRegistrada ?? mark.hora,
      });
      setStatus('done');
    } catch (requestError) {
      setError(friendlyError(requestError));
      setStatus('idle');
    }
  }

  const isReading = status === 'reading';

  return (
    <main className="mark-page">
      <section className="mark-shell compact-mark-shell">
        <header className="mark-header">
          <h1>Control de asistencia</h1>
          <p className="mark-clock">{new Date().toLocaleDateString('es-GT')}</p>
        </header>

        <section className="reader-panel simple-reader-panel" aria-live="polite">
          <p className="reader-title">
            {isReading ? 'Leyendo huella...' : 'Presione MARCAR y coloque su dedo sobre el lector'}
          </p>
          {isReading && <p className="muted">Coloque su dedo en el lector</p>}

          <button
            className="mark-primary-button"
            type="button"
            disabled={isReading}
            onClick={markAttendance}
          >
            {isReading ? 'LEYENDO...' : 'MARCAR'}
          </button>

          {error && (
            <div className="error-message mark-result">
              <strong>{error}</strong>
              <span>Intentar nuevamente</span>
            </div>
          )}

          {result && (
            <div className="success-message mark-result">
              <strong>Marcación realizada correctamente</strong>
              <span>Función: {result.tipo}</span>
              <span>Hora registrada: {result.hora}</span>
            </div>
          )}
        </section>

        <Link className="secondary-link" to="/">
          Volver
        </Link>
      </section>
    </main>
  );
}
