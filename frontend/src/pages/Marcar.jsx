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
    return 'Huella no reconocida. La huella no corresponde a ningún trabajador registrado.';
  }
  if (code === 'SDK_NO_DISPONIBLE') {
    return 'No se encontraron los componentes necesarios de ZKFinger SDK.';
  }
  if (code === 'LECTOR_NO_DETECTADO') {
    return 'Lector ZKTeco ZK9500 no detectado. Verifique la conexión USB.';
  }
  if (code === 'LECTOR_NO_DISPONIBLE') {
    return 'Lector ZKTeco ZK9500 no disponible. Verifique la conexión USB.';
  }
  if (code === 'BACKEND_OFFLINE' || code === 'BACKEND_NO_DISPONIBLE') {
    return 'No se pudo conectar con el sistema.';
  }
  if (code === 'AGENT_NO_AUTORIZADO' || code === 'AGENT_TOKEN_NO_CONFIGURADO') {
    return 'El servicio biométrico no está autorizado. Solicite asistencia al administrador.';
  }
  if (code === 'TEMPLATES_NO_DISPONIBLES') {
    return 'No hay huellas disponibles para identificar. Solicite el registro de su huella.';
  }
  if (code === 'ERROR_CARGA_TEMPLATES') {
    return 'No se pudieron preparar las huellas registradas. Intente nuevamente.';
  }
  if (code === 'CAPTURE_TIMEOUT') {
    return 'No se detectó ninguna huella. Intente nuevamente.';
  }
  if (code === 'ERROR_ZK9500' || code === 'DEVICE_STATUS_FAILED') {
    return 'No se pudo completar la lectura en el ZKTeco ZK9500. Intente nuevamente.';
  }
  if (code === 'AGENT_OFFLINE' || (!requestError.response && requestError.request)) {
    return 'Servicio biometrico no disponible. Instale o inicie ControlHorarioBiometricAgent en esta computadora.';
  }
  if (code === 'HORARIO_NO_ASIGNADO') {
    return 'No se puede realizar la marcación. No tiene un horario asignado para esta jornada.';
  }
  if (code === 'TRABAJADOR_INACTIVO') {
    return 'No se puede realizar la marcación. Consulte con el administrador.';
  }
  if (code === 'JORNADA_COMPLETADA') {
    return 'Jornada completada. Ya se registraron todas las marcaciones correspondientes.';
  }
  if (code === 'MARCACION_RECIENTE') {
    return 'La marcación ya se está procesando. Intente nuevamente en unos segundos.';
  }
  if (requestError.code === 'ECONNABORTED') {
    return 'No se detectó ninguna huella. Intente nuevamente.';
  }
  return requestError.response?.data?.message ?? 'No se pudo realizar la marcación.';
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
              <strong>Marcación realizada correctamente</strong>
              <span>Funcion: {result.tipo}</span>
              <span>Hora registrada: {result.hora}</span>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
