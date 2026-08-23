import axios from 'axios';

function resolveApiBaseUrl() {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  const hostname = window.location.hostname || 'localhost';
  return `http://${hostname}:5000/api`;
}

const api = axios.create({
  baseURL: resolveApiBaseUrl(),
  timeout: 10000,
  withCredentials: true,
});

let csrfToken = sessionStorage.getItem('csrfToken') ?? '';

api.interceptors.request.use((config) => {
  const method = config.method?.toUpperCase();
  if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    config.headers['X-CSRF-Token'] = csrfToken;
  }
  return config;
});

api.interceptors.response.use((response) => {
  const token = response.data?.data?.csrf_token;
  if (token) {
    csrfToken = token;
    sessionStorage.setItem('csrfToken', token);
  }
  return response;
});

export default api;
