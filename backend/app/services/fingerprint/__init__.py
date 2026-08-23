from flask import current_app

from app.services.fingerprint.mock_provider import MockFingerprintProvider
from app.services.fingerprint.real_provider import RealFingerprintProvider


def get_fingerprint_provider():
    provider = current_app.config.get("FINGERPRINT_PROVIDER", "mock")
    if provider == "mock":
        return MockFingerprintProvider()
    if provider in {"zk9500", "real"}:
        return RealFingerprintProvider()
    raise ValueError(f"Proveedor biometrico no soportado: {provider}")
