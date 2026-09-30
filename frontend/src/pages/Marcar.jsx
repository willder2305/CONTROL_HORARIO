/**
 * Modulo de interfaz Marcar del sistema de control de horarios.
 * Mantiene la responsabilidad indicada sin duplicar logica de dominio del backend.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { registrarMarcacionBiometrica } from '../services/marcacionService';

/**
 * Centraliza una decision de configuracion o la traduccion de errores para conservar una experiencia consistente.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
function friendlyError(requestError) {
  const code = requestError.response?.data?.code;
  if (code === 'HUELLA_NO_RECONOCIDA') {
    return 'Huella no reconocida. La huella no se encuentra registrada.';
  }
  if (code === 'LECTOR_NO_DISPONIBLE' || code === 'LECTOR_NO_DETECTADO') {
    return 'Lector de huellas no disponible. Verifique la conexion del ZKTeco ZK9500.';
  }
  if (code === 'AGENT_OFFLINE' || (!requestError.response && requestError.request)) {
    return 'Servicio biometrico no disponible. Instale o inicie ControlHorarioBiometricAgent en esta computadora.';
  }
  if (code === 'HORARIO_NO_ASIGNADO') {
    return 'No se puede realizar la marcacion. No tiene un horario asignado para esta jornada.';
  }
  if (code === 'TRABAJADOR_INACTIVO') {
    return 'No se puede realizar la marcacion. Consulte con el administrador.';
  }
  if (code === 'JORNADA_COMPLETADA') {
    return 'Jornada completada. Ya se registraron todas las marcaciones de esta jornada.';
  }
  if (code === 'MARCACION_RECIENTE') {
    return 'La marcacion ya se esta procesando. Intente nuevamente en unos segundos.';
  }
  if (requestError.code === 'ECONNABORTED') {
    return 'No se detecto ninguna huella. Intente nuevamente.';
  }
  return requestError.response?.data?.message ?? 'No se pudo realizar la marcacion.';
}

/**
 * Renderiza el flujo publico de asistencia y delega la identificacion al agente biometrico configurado.
 *
 * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
 */
export default function Marcar() {
  const navigate = useNavigate();
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  /**
   * Solicita identificacion biometrica y muestra el tipo y la hora de la marcacion calculada por el backend. Marcar.jsx.
   *
   * @returns {JSX.Element|Promise<unknown>|unknown} Resultado de la operacion o elemento renderizado.
   */
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

  /**
   * Abre el inicio de sesion administrativo desde el acceso de reloj de la vista publica.
   */
  function openAdministrativeAccess() {
    navigate('/admin/login');
  }

  const isReading = status === 'reading';

  return (
    <main className="mark-page">
      <button
        aria-label="Acceso administrativo"
        className="mark-admin-access-icon"
        onClick={openAdministrativeAccess}
        title="Acceso administrativo"
        type="button"
      >
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="8.5" />
          <path d="M12 7.5v5l3.25 2" />
        </svg>
      </button>
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
              <strong>Marcacion realizada correctamente</strong>
              <span>Funcion: {result.tipo}</span>
              <span>Hora registrada: {result.hora}</span>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
