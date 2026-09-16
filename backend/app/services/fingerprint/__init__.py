"""Modulo   init   del sistema de control de horarios.

Agrupa la logica propia necesaria para esta responsabilidad sin exponer detalles de infraestructura.
"""

from flask import current_app

from app.services.fingerprint.local_agent_provider import LocalAgentFingerprintProvider
from app.services.fingerprint.mock_provider import MockFingerprintProvider
from app.services.fingerprint.real_provider import RealFingerprintProvider


def get_fingerprint_provider():
    """
    Resuelve el provider biometrico configurado para el entorno sin acoplar las rutas a una implementacion concreta.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    provider = current_app.config.get("FINGERPRINT_PROVIDER", "mock")
    if provider == "mock":
        return MockFingerprintProvider()
    if provider in {"zk9500", "real"}:
        return RealFingerprintProvider()
    if provider == "local_agent":
        return LocalAgentFingerprintProvider()
    raise ValueError(f"Proveedor biometrico no soportado: {provider}")
