import { createBrowserRouter } from 'react-router-dom';

import Home from '../pages/Home.jsx';
import Marcar from '../pages/Marcar.jsx';
import ProtectedRoute from '../components/ProtectedRoute.jsx';
import Configuracion from '../pages/admin/Configuracion.jsx';
import Dashboard from '../pages/admin/Dashboard.jsx';
import Horarios from '../pages/admin/Horarios.jsx';
import Login from '../pages/admin/Login.jsx';
import Marcaciones from '../pages/admin/Marcaciones.jsx';
import Reportes from '../pages/admin/Reportes.jsx';
import Trabajadores from '../pages/admin/Trabajadores.jsx';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Home />,
  },
  {
    path: '/admin/login',
    element: <Login />,
  },
  {
    path: '/admin',
    element: (
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/trabajadores',
    element: (
      <ProtectedRoute>
        <Trabajadores />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/horarios',
    element: (
      <ProtectedRoute>
        <Horarios />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/marcaciones',
    element: (
      <ProtectedRoute>
        <Marcaciones />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/reportes',
    element: (
      <ProtectedRoute>
        <Reportes />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/configuracion',
    element: (
      <ProtectedRoute>
        <Configuracion />
      </ProtectedRoute>
    ),
  },
  {
    path: '/marcar',
    element: <Marcar />,
  },
]);

export default router;
