from types import SimpleNamespace

from app.services.fingerprint.real_provider import (
    FingerprintDeviceError,
    FingerprintDuplicateError,
    RealFingerprintProvider,
)


class FakeZKFP2:
    def __init__(self, captures=None, device_count=1):
        self.captures = list(captures or [])
        self.device_count = device_count
        self.database = {}
        self.db_initialized = False
        self.terminated = False

    def Init(self):
        return 0

    def GetDeviceCount(self):
        return self.device_count

    def OpenDevice(self, index):
        return 0

    def DBInit(self):
        self.db_initialized = True
        return 1

    def DBFree(self):
        self.db_initialized = False
        return 0

    def CloseDevice(self):
        return 0

    def Terminate(self):
        self.terminated = True
        return 0

    def AcquireFingerprint(self):
        if not self.captures:
            return None
        capture = self.captures.pop(0)
        if capture is None:
            return None
        return capture, b"image"

    def DBMatch(self, template_a, template_b):
        return 10 if template_a[:1] == template_b[:1] else 0

    def DBMerge(self, template_a, template_b, template_c):
        assert self.db_initialized is True
        return b"MERGED:" + template_a + template_b + template_c, 0

    def DBClear(self):
        assert self.db_initialized is True
        self.database.clear()
        return 0

    def DBAdd(self, fingerprint_id, template):
        assert self.db_initialized is True
        self.database[fingerprint_id] = template
        return 0

    def DBIdentify(self, captured_template):
        assert self.db_initialized is True
        for fingerprint_id, template in self.database.items():
            if self.DBMatch(captured_template, template) > 0:
                return fingerprint_id, 10
        return 0, 0


def test_real_provider_enroll_merges_three_zkteco_samples():
    provider = RealFingerprintProvider(
        sdk_factory=lambda: FakeZKFP2(captures=[b"A1", None, b"A2", None, b"A3"]),
        capture_timeout_seconds=1,
    )

    template = provider.enroll()

    assert template == b"MERGED:A1A2A3"


def test_real_provider_enroll_rejects_duplicate_fingerprint():
    fingerprint_a = SimpleNamespace(id=1, template_biometrico=b"A-template")
    provider = RealFingerprintProvider(
        sdk_factory=lambda: FakeZKFP2(captures=[b"A-live"]),
        capture_timeout_seconds=1,
    )

    try:
        provider.enroll(active_fingerprints=[fingerprint_a])
    except FingerprintDuplicateError as error:
        assert "registrada" in str(error)
    else:
        raise AssertionError("Expected FingerprintDuplicateError")


def test_real_provider_identifies_against_active_templates():
    fingerprint_a = SimpleNamespace(id=1, template_biometrico=b"A-template")
    fingerprint_b = SimpleNamespace(id=2, template_biometrico=b"B-template")
    provider = RealFingerprintProvider(
        sdk_factory=lambda: FakeZKFP2(captures=[b"B-live"]),
        capture_timeout_seconds=1,
    )

    identified = provider.identify(active_fingerprints=[fingerprint_a, fingerprint_b])

    assert identified is fingerprint_b


def test_real_provider_reports_missing_device():
    provider = RealFingerprintProvider(
        sdk_factory=lambda: FakeZKFP2(device_count=0),
        capture_timeout_seconds=1,
    )

    try:
        provider.enroll()
    except FingerprintDeviceError as error:
        assert "No se detecto lector" in str(error)
    else:
        raise AssertionError("Expected FingerprintDeviceError")


def test_real_provider_verify_uses_match_threshold():
    provider = RealFingerprintProvider(
        sdk_factory=lambda: FakeZKFP2(captures=[b"A-live"]),
        capture_timeout_seconds=1,
        match_threshold=1,
    )

    assert provider.verify(template_biometrico=b"A-template") is True
    assert provider.verify(template_biometrico=b"B-template") is False
