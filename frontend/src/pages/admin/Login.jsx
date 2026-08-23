import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { login } from '../../services/authService';

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ usuario: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function handleChange(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(form.usuario, form.password);
      navigate('/admin', { replace: true });
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ?? 'No se pudo iniciar sesión.',
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="content-panel">
        <p className="eyebrow">Administrador</p>
        <h1>Inicio de sesión</h1>
        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            Usuario
            <input
              type="text"
              name="usuario"
              autoComplete="username"
              value={form.usuario}
              onChange={handleChange}
              required
            />
          </label>
          <label>
            Contraseña
            <input
              type="password"
              name="password"
              autoComplete="current-password"
              value={form.password}
              onChange={handleChange}
              required
            />
          </label>
          {error && <p className="error-message">{error}</p>}
          <button type="submit" disabled={loading}>
            {loading ? 'Validando...' : 'Ingresar'}
          </button>
        </form>
        <Link className="secondary-link" to="/">
          Volver
        </Link>
      </section>
    </main>
  );
}
