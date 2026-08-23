import { NavLink, useNavigate } from 'react-router-dom';

import { logout } from '../services/authService';

const adminLinks = [
  ['Dashboard', '/admin'],
  ['Trabajadores', '/admin/trabajadores'],
  ['Horarios', '/admin/horarios'],
  ['Marcaciones', '/admin/marcaciones'],
  ['Reportes', '/admin/reportes'],
  ['Configuración', '/admin/configuracion'],
];

export default function AdminNav() {
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/admin/login', { replace: true });
  }

  function renderLinks() {
    return adminLinks.map(([label, path]) => (
      <NavLink
        className={({ isActive }) => (isActive ? 'admin-nav-link active' : 'admin-nav-link')}
        end={path === '/admin'}
        key={path}
        to={path}
      >
        {label}
      </NavLink>
    ));
  }

  return (
    <>
      <nav className="admin-nav desktop-admin-nav" aria-label="Navegación administrativa">
        {renderLinks()}
        <button className="admin-nav-link logout-link" type="button" onClick={handleLogout}>
          Cerrar sesión
        </button>
      </nav>
      <details className="admin-menu">
        <summary>Menú</summary>
        <nav className="admin-nav mobile-admin-nav" aria-label="Navegación administrativa móvil">
          {renderLinks()}
          <button className="admin-nav-link logout-link" type="button" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </nav>
      </details>
    </>
  );
}
