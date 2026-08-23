import axios from 'axios';

function resolveAgentBaseUrl() {
  return import.meta.env.VITE_BIOMETRIC_AGENT_URL || 'http://127.0.0.1:8765';
}

export function useLocalAgent() {
  return import.meta.env.VITE_BIOMETRIC_MODE === 'local-agent';
}

const agentApi = axios.create({
  baseURL: resolveAgentBaseUrl(),
  timeout: 65000,
  withCredentials: false,
});

export async function getAgentStatus() {
  const response = await agentApi.get('/device/status', { timeout: 12000 });
  return response.data;
}

export async function enrollFingerprintWithAgent() {
  const response = await agentApi.post('/enroll', {}, { timeout: 90000 });
  return response.data;
}

export async function identifyAndMarkWithAgent() {
  const response = await agentApi.post('/identify-and-mark', {}, { timeout: 65000 });
  return response.data;
}
