/**
 * Modulo de interfaz Loading del sistema de control de horarios.
 * Mantiene la responsabilidad indicada sin duplicar logica de dominio del backend.
 */
export default function Loading({ text = 'Cargando...' }) {
  return <p className="muted">{text}</p>;
}
