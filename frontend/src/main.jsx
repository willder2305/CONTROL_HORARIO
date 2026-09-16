/**
 * Modulo de interfaz main del sistema de control de horarios.
 * Mantiene la responsabilidad indicada sin duplicar logica de dominio del backend.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';

import router from './router/router.jsx';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
