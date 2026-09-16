"""Modulo local agent provider del sistema de control de horarios.

Agrupa la logica propia necesaria para esta responsabilidad sin exponer detalles de infraestructura.
"""

from app.services.fingerprint.base import FingerprintProvider
from app.services.fingerprint.real_provider import FingerprintDeviceError


class LocalAgentFingerprintProvider(FingerprintProvider):
    """
    Representa LocalAgentFingerprintProvider dentro del dominio de control de horarios.

    Centraliza los datos y el comportamiento asociados a esta entidad o servicio.
    """
    provider_name = "local_agent"
    version = "ControlHorarioBiometricAgent"

    def enroll(self, fingerprint_id=None, active_fingerprints=None):
        """
        Define la captura y generacion de un template biometrico para cualquier provider compatible.

        Args:
            fingerprint_id: Dato utilizado por la operacion.
            active_fingerprints: Dato utilizado por la operacion.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        raise FingerprintDeviceError(
            "El servidor esta configurado para agente biometrico local. "
            "La captura debe realizarse desde ControlHorarioBiometricAgent."
        )

    def identify(self, fingerprint_id=None, active_fingerprints=None):
        """
        Define la busqueda de una huella contra los templates activos del provider.

        Args:
            fingerprint_id: Dato utilizado por la operacion.
            active_fingerprints: Dato utilizado por la operacion.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        raise FingerprintDeviceError(
            "El servidor esta configurado para agente biometrico local. "
            "La identificacion debe realizarse desde ControlHorarioBiometricAgent."
        )

    def verify(self, fingerprint_id=None, template_biometrico=None):
        """
        Define la comparacion uno a uno entre una captura y un template almacenado.

        Args:
            fingerprint_id: Dato utilizado por la operacion.
            template_biometrico: Dato utilizado por la operacion.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        return False

    def status(self):
        """
        Describe la disponibilidad del provider, SDK y dispositivo sin exponer templates biometricos.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        return {
            "provider": self.provider_name,
            "ready": True,
            "message": "La lectura biometrica se realiza desde el agente local instalado en la PC de marcaje.",
        }
