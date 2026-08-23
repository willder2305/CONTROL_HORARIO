from abc import ABC, abstractmethod


class FingerprintProvider(ABC):
    @abstractmethod
    def enroll(self, fingerprint_id=None, active_fingerprints=None):
        pass

    @abstractmethod
    def identify(self, fingerprint_id=None, active_fingerprints=None):
        pass

    @abstractmethod
    def verify(self, fingerprint_id=None, template_biometrico=None):
        pass

    def status(self):
        return {
            "provider": getattr(self, "provider_name", "unknown"),
            "ready": False,
        }
