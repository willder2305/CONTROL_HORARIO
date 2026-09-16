"""Modulo mock provider del sistema de control de horarios.

Agrupa la logica propia necesaria para esta responsabilidad sin exponer detalles de infraestructura.
"""

from app.services.fingerprint.base import FingerprintProvider


class MockFingerprintProvider(FingerprintProvider):
    """
    Representa MockFingerprintProvider dentro del dominio de control de horarios.

    Centraliza los datos y el comportamiento asociados a esta entidad o servicio.
    """
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
        """
        Define la busqueda de una huella contra los templates activos del provider.

        Args:
            fingerprint_id: Dato utilizado por la operacion.
            active_fingerprints: Dato utilizado por la operacion.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        template = self.enroll(fingerprint_id)
        for fingerprint in active_fingerprints:
            if fingerprint.template_biometrico == template:
                return fingerprint
        return None

    def verify(self, fingerprint_id=None, template_biometrico=None):
        """
        Define la comparacion uno a uno entre una captura y un template almacenado.

        Args:
            fingerprint_id: Dato utilizado por la operacion.
            template_biometrico: Dato utilizado por la operacion.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        return self.enroll(fingerprint_id) == template_biometrico

    def status(self):
        """
        Describe la disponibilidad del provider, SDK y dispositivo sin exponer templates biometricos.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
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
        """
        Implementa la responsabilidad de  normalize dentro de este modulo.

        Args:
            fingerprint_id: Dato utilizado por la operacion.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        return (fingerprint_id or "").strip().upper()
