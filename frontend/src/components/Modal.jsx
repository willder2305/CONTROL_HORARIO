/**
 * Modulo de interfaz Modal del sistema de control de horarios.
 * Mantiene la responsabilidad indicada sin duplicar logica de dominio del backend.
 */
export default function Modal({ children }) {
  return <div className="modal">{children}</div>;
}
