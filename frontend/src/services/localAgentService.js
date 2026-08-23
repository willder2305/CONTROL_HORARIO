import axios from "axios";

function resolveAgentBaseUrl() {
  return import.meta.env.VITE_BIOMETRIC_AGENT_URL || "http://127.0.0.1:8765";
}

export function useLocalAgent() {
  return import.meta.env.VITE_BIOMETRIC_MODE === "local-agent";
}

const agentApi = axios.create({
  baseURL: resolveAgentBaseUrl(),
  timeout: 65000,
  withCredentials: false,
});

function localAgentError(code, message) {
  const error = new Error(message);
  error.response = { data: { code, message } };
  return error;
}

function emitProgress(onProgress, message) {
  if (typeof onProgress === "function") {
    onProgress(message);
  }
}

export async function getAgentHealth() {
  try {
    const response = await agentApi.get("/health", { timeout: 8000 });
    return response.data;
  } catch (error) {
    throw localAgentError("AGENT_OFFLINE", "Servicio biometrico no disponible.");
  }
}

export async function getBiometricDeviceStatus() {
  const response = await agentApi.get("/device/status", { timeout: 12000 });
  return response.data;
}

export async function getAgentStatus() {
  return getBiometricDeviceStatus();
}

async function ensureAgentAndDeviceReady(onProgress) {
  emitProgress(onProgress, "Comprobando lector...");
  await getAgentHealth();
  let status;
  try {
    status = await getBiometricDeviceStatus();
  } catch (error) {
    throw localAgentError("DEVICE_STATUS_FAILED", "No se pudo consultar el estado del lector.");
  }

  const device = status.data || status;
  if (device.sdkLoaded === false) {
    throw localAgentError("SDK_NO_DISPONIBLE", "No se encontraron los componentes necesarios de ZKFinger SDK.");
  }
  if (device.connected === false) {
    throw localAgentError("LECTOR_NO_DETECTADO", "Lector de huellas no detectado. Conecte el ZKTeco ZK9500.");
  }
  if (device.ready === false) {
    throw localAgentError("LECTOR_NO_DISPONIBLE", "Lector de huellas no disponible.");
  }
  emitProgress(onProgress, "ZK9500 conectado");
  return status;
}

export async function enrollFingerprintWithAgent(options = {}) {
  await ensureAgentAndDeviceReady(options.onProgress);
  emitProgress(options.onProgress, "Coloque su dedo. Captura 1 de 3.");
  emitProgress(options.onProgress, "Retire el dedo cuando el lector lo indique.");
  emitProgress(options.onProgress, "Captura 2 de 3 y captura 3 de 3.");
  const response = await agentApi.post("/enroll", {}, { timeout: 90000 });
  emitProgress(options.onProgress, "Huella registrada correctamente");
  return response.data;
}

export async function captureFingerprintWithAgent(options = {}) {
  return enrollFingerprintWithAgent(options);
}

export async function identifyAndMarkWithAgent(options = {}) {
  await ensureAgentAndDeviceReady(options.onProgress);
  try {
    const response = await agentApi.post("/identify-and-mark", {}, { timeout: 65000 });
    return response.data;
  } catch (error) {
    if (error.response?.data?.code === "AGENT_ERROR") {
      throw localAgentError("BACKEND_OFFLINE", "No se pudo conectar con el sistema.");
    }
    throw error;
  }
}
