from app.services.fingerprint.base import FingerprintProvider
from app.services.fingerprint.real_provider import FingerprintDeviceError


class LocalAgentFingerprintProvider(FingerprintProvider):
    provider_name = "local_agent"
    version = "ControlHorarioBiometricAgent"

    def enroll(self, fingerprint_id=None, active_fingerprints=None):
        raise FingerprintDeviceError(
            "El servidor esta configurado para agente biometrico local. "
            "La captura debe realizarse desde ControlHorarioBiometricAgent."
        )

    def identify(self, fingerprint_id=None, active_fingerprints=None):
        raise FingerprintDeviceError(
            "El servidor esta configurado para agente biometrico local. "
            "La identificacion debe realizarse desde ControlHorarioBiometricAgent."
        )

    def verify(self, fingerprint_id=None, template_biometrico=None):
        return False

    def status(self):
        return {
            "provider": self.provider_name,
            "ready": True,
            "message": "La lectura biometrica se realiza desde el agente local instalado en la PC de marcaje.",
        }
