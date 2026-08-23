from app.services.fingerprint.base import FingerprintProvider


class MockFingerprintProvider(FingerprintProvider):
    provider_name = "mock"
    version = "mock-v1"

    def enroll(self, fingerprint_id=None, active_fingerprints=None):
        """
        Genera un template biometrico simulado desde un identificador de desarrollo.

        Recibe:
            fingerprint_id, por ejemplo FP0001.

        Utilizado desde:
            Endpoint administrativo de registro de huella.

        Retorna:
            Bytes del template simulado.
        """
        normalized = self._normalize(fingerprint_id)
        if not normalized:
            raise ValueError("La huella simulada es obligatoria.")
        template = f"MOCK::{normalized}".encode("utf-8")
        for fingerprint in active_fingerprints or []:
            if fingerprint.template_biometrico == template:
                from app.services.fingerprint.real_provider import FingerprintDuplicateError

                raise FingerprintDuplicateError("Esta huella ya se encuentra registrada en el sistema.")
        return template

    def identify(self, fingerprint_id=None, active_fingerprints=None):
        template = self.enroll(fingerprint_id)
        for fingerprint in active_fingerprints:
            if fingerprint.template_biometrico == template:
                return fingerprint
        return None

    def verify(self, fingerprint_id=None, template_biometrico=None):
        return self.enroll(fingerprint_id) == template_biometrico

    def status(self):
        return {
            "provider": self.provider_name,
            "sdkLoaded": True,
            "deviceCount": 0,
            "connected": True,
            "opened": True,
            "ready": True,
            "mode": "mock",
        }

    def _normalize(self, fingerprint_id):
        return (fingerprint_id or "").strip().upper()
