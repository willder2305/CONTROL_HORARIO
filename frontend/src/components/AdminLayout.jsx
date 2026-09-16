/**
 * Modulo de interfaz AdminLayout del sistema de control de horarios.
 * Mantiene la responsabilidad indicada sin duplicar logica de dominio del backend.
 */
export default function AdminLayout({ children }) {
  return <main className="page">{children}</main>;
}
