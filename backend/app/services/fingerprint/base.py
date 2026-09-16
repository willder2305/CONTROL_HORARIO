"""Modulo base del sistema de control de horarios.

Agrupa la logica propia necesaria para esta responsabilidad sin exponer detalles de infraestructura.
"""

from abc import ABC, abstractmethod


class FingerprintProvider(ABC):
    """
    Representa FingerprintProvider dentro del dominio de control de horarios.

    Define el contrato o comportamiento compartido por sus implementaciones.
    """
    @abstractmethod
    def enroll(self, fingerprint_id=None, active_fingerprints=None):
        """
        Define la captura y generacion de un template biometrico para cualquier provider compatible.

        Args:
            fingerprint_id: Dato utilizado por la operacion.
            active_fingerprints: Dato utilizado por la operacion.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        pass

    @abstractmethod
    def identify(self, fingerprint_id=None, active_fingerprints=None):
        """
        Define la busqueda de una huella contra los templates activos del provider.

        Args:
            fingerprint_id: Dato utilizado por la operacion.
            active_fingerprints: Dato utilizado por la operacion.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        pass

    @abstractmethod
    def verify(self, fingerprint_id=None, template_biometrico=None):
        """
        Define la comparacion uno a uno entre una captura y un template almacenado.

        Args:
            fingerprint_id: Dato utilizado por la operacion.
            template_biometrico: Dato utilizado por la operacion.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        pass

    def status(self):
        """
        Describe la disponibilidad del provider, SDK y dispositivo sin exponer templates biometricos.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        return {
            "provider": getattr(self, "provider_name", "unknown"),
            "ready": False,
        }
