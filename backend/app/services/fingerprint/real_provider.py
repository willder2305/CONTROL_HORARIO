import logging
import base64
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from time import monotonic, sleep

from flask import current_app, has_app_context

from app.services.fingerprint.base import FingerprintProvider


class FingerprintDeviceError(RuntimeError):
    pass


class FingerprintDuplicateError(RuntimeError):
    pass


class RealFingerprintProvider(FingerprintProvider):
    provider_name = "zk9500"
    version = "ZKFinger Standard SDK 5.3.0.33"

    def __init__(
        self,
        sdk_factory=None,
        device_index=None,
        capture_timeout_seconds=None,
        enroll_samples=None,
        match_threshold=None,
    ):
        self.sdk_factory = sdk_factory
        self.device_index = self._config_int("ZKTECO_DEVICE_INDEX", 0, device_index)
        self.capture_timeout_seconds = self._config_int(
            "ZKTECO_CAPTURE_TIMEOUT_SECONDS",
            30,
            capture_timeout_seconds,
        )
        self.enroll_samples = self._config_int("ZKTECO_ENROLL_SAMPLES", 3, enroll_samples)
        self.match_threshold = self._config_int("ZKTECO_MATCH_THRESHOLD", 1, match_threshold)
        self.release_timeout_seconds = 10
        self.logger = logging.getLogger("biometric")
        self.bridge_path = (
            Path(__file__).resolve().parents[3]
            / "zk9500_bridge"
            / "bin"
            / "Zk9500Bridge.exe"
        )

    def enroll(self, fingerprint_id=None, active_fingerprints=None):
        """
        Captura tres muestras desde el lector ZKTeco ZK9500 y genera un template.

        Recibe:
            fingerprint_id opcional, ignorado en modo real.

        Utilizado desde:
            POST /api/biometria/trabajadores/<id>/registrar.

        Retorna:
            Template biometrico binario compatible con ZKFinger V10.0.
        """
        if self._should_use_bridge():
            return self._bridge_enroll(active_fingerprints or [])

        device = self._open_device()
        try:
            self._load_fingerprints_into_database(device, active_fingerprints or [])
            templates = self._capture_enrollment_templates(device)
            self._validate_same_finger(device, templates)
            return self._merge_templates(device, templates)
        finally:
            self._terminate_device(device)

    def identify(self, fingerprint_id=None, active_fingerprints=None):
        """
        Identifica una huella capturada contra templates activos de la base de datos.

        Recibe:
            fingerprint_id opcional, ignorado en modo real.
            active_fingerprints: registros Huella activos.

        Utilizado desde:
            services/attendance_service.py y /api/biometria/identificar.

        Retorna:
            Huella coincidente o None.
        """
        fingerprints = list(active_fingerprints or [])
        if not fingerprints:
            return None

        if self._should_use_bridge():
            return self._bridge_identify(fingerprints)

        device = self._open_device()
        try:
            captured_template = self._capture_template(device)
            return self._identify_with_database(device, captured_template, fingerprints)
        finally:
            self._terminate_device(device)

    def verify(self, fingerprint_id=None, template_biometrico=None):
        """
        Compara una huella capturada contra un template almacenado.

        Recibe:
            fingerprint_id opcional, ignorado en modo real.
            template_biometrico almacenado.

        Utilizado desde:
            Validaciones biometrica 1:1 futuras.

        Retorna:
            True si la comparacion alcanza el umbral configurado.
        """
        if not template_biometrico:
            return False

        device = self._open_device()
        try:
            captured_template = self._capture_template(device)
            return self._match(device, captured_template, template_biometrico) >= self.match_threshold
        finally:
            self._terminate_device(device)

    def status(self):
        if self._should_use_bridge():
            return self._bridge_status()

        status = {
            "provider": self.provider_name,
            "sdkLoaded": False,
            "deviceCount": 0,
            "connected": False,
            "opened": False,
            "ready": False,
            "deviceIndex": self.device_index,
            "sdkVersion": self.version,
        }
        device = None
        try:
            sdk_class = self._load_sdk_factory()
            status["sdkLoaded"] = True
            device = sdk_class()
            init_result = self._call(device, "Init")
            if init_result not in (None, 0):
                status["error"] = f"No se pudo inicializar ZKFinger SDK. Codigo: {init_result}"
                return status
            device_count = self._call(device, "GetDeviceCount") or 0
            status["deviceCount"] = device_count
            status["connected"] = device_count > self.device_index
            if not status["connected"]:
                return status
            open_result = self._call(device, "OpenDevice", self.device_index)
            status["opened"] = not (isinstance(open_result, int) and open_result < 0)
            status["ready"] = status["opened"]
            return status
        except Exception as error:
            status["error"] = str(error)
            return status
        finally:
            self._terminate_device(device)

    def _should_use_bridge(self):
        return self.sdk_factory is None and self.bridge_path.exists()

    def _bridge_status(self):
        result = self._run_bridge(["status"], timeout=20)
        data = self._parse_bridge_output(result.stdout)
        return {
            "provider": self.provider_name,
            "sdkLoaded": data.get("sdkLoaded") == "true",
            "deviceCount": int(data.get("deviceCount", "0") or 0),
            "connected": data.get("connected") == "true",
            "opened": data.get("opened") == "true",
            "ready": data.get("ready") == "true",
            "deviceIndex": self.device_index,
            "sdkVersion": self.version,
            "error": data.get("error"),
            "bridge": str(self.bridge_path),
        }

    def _bridge_enroll(self, active_fingerprints):
        with self._template_file(active_fingerprints) as templates_path:
            result = self._run_bridge(
                [
                    "enroll",
                    "--templates",
                    templates_path,
                    "--timeout",
                    str(self.capture_timeout_seconds),
                ],
                timeout=self.capture_timeout_seconds + 25,
            )
        data = self._parse_bridge_output(result.stdout)
        self._raise_for_bridge_error(data, result)
        template = data.get("template")
        if not template:
            raise FingerprintDeviceError("El servicio ZK9500 no devolvio template biometrico.")
        return base64.b64decode(template)

    def _bridge_identify(self, active_fingerprints):
        with self._template_file(active_fingerprints) as templates_path:
            result = self._run_bridge(
                [
                    "identify",
                    "--templates",
                    templates_path,
                    "--timeout",
                    str(self.capture_timeout_seconds),
                ],
                timeout=self.capture_timeout_seconds + 15,
            )
        data = self._parse_bridge_output(result.stdout)
        if data.get("code") == "HUELLA_NO_RECONOCIDA":
            return None
        self._raise_for_bridge_error(data, result)
        identified_id = int(data.get("id", "0") or 0)
        for fingerprint in active_fingerprints:
            if fingerprint.id == identified_id:
                return fingerprint
        return None

    def _run_bridge(self, args, timeout):
        completed = subprocess.run(
            [str(self.bridge_path), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(self.bridge_path.parent),
        )
        if completed.stderr:
            for line in completed.stderr.splitlines():
                self._log(line.replace("[BIOMETRIC] ", ""))
        return completed

    def _raise_for_bridge_error(self, data, result):
        if result.returncode == 0 and data.get("success", "true") != "false":
            return
        code = data.get("code")
        message = data.get("message") or data.get("error") or result.stderr or "Error del servicio ZK9500."
        if code == "HUELLA_DUPLICADA":
            raise FingerprintDuplicateError(message)
        raise FingerprintDeviceError(message)

    def _parse_bridge_output(self, output):
        data = {}
        for line in (output or "").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()
        return data

    @contextmanager
    def _template_file(self, fingerprints):
        temp_file = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
        try:
            for fingerprint in fingerprints:
                encoded = base64.b64encode(fingerprint.template_biometrico).decode("ascii")
                temp_file.write(f"{fingerprint.id}|{encoded}\n")
            temp_file.close()
            yield temp_file.name
        finally:
            try:
                Path(temp_file.name).unlink(missing_ok=True)
            except OSError:
                pass

    def _config_int(self, key, default, explicit_value):
        if explicit_value is not None:
            return int(explicit_value)
        if has_app_context():
            return int(current_app.config.get(key, default))
        return default

    def _load_sdk_factory(self):
        if self.sdk_factory:
            return self.sdk_factory
        try:
            from pyzkfp import ZKFP2
        except ImportError as error:
            raise FingerprintDeviceError(
                "No se encontro el wrapper ZKFP2. Instale el ZKFinger SDK for Windows, "
                "su driver oficial y un wrapper Python compatible antes de usar FINGERPRINT_PROVIDER=real."
            ) from error
        return ZKFP2

    def _open_device(self):
        self._log("Provider: zk9500")
        self._log("Inicializando ZKFinger SDK 5.3.0.33")
        sdk_class = self._load_sdk_factory()
        device = sdk_class()

        init_result = self._call(device, "Init")
        if init_result not in (None, 0):
            raise FingerprintDeviceError(f"No se pudo inicializar ZKFinger SDK. Codigo: {init_result}")
        self._log("SDK inicializado")

        self._log("Buscando lector")
        device_count = self._call(device, "GetDeviceCount")
        self._log(f"Dispositivos encontrados: {device_count or 0}")
        if not device_count or device_count <= self.device_index:
            self._terminate_device(device)
            raise FingerprintDeviceError("No se detecto lector ZKTeco ZK9500 conectado.")

        self._log(f"Abriendo dispositivo {self.device_index}")
        open_result = self._call(device, "OpenDevice", self.device_index)
        if isinstance(open_result, int) and open_result < 0:
            self._terminate_device(device)
            raise FingerprintDeviceError(f"No se pudo abrir el lector ZK9500. Codigo: {open_result}")

        db_result = self._call_if_exists(device, "DBInit")
        if isinstance(db_result, int) and db_result < 0:
            self._terminate_device(device)
            raise FingerprintDeviceError(
                f"No se pudo inicializar la base biometrica ZKFinger. Codigo: {db_result}"
            )

        self._log("ZK9500 listo")
        return device

    def _capture_enrollment_templates(self, device):
        templates = []
        while len(templates) < self.enroll_samples:
            template = self._capture_template(device)
            duplicated_id = self._identify_loaded_template(device, template)
            if duplicated_id:
                raise FingerprintDuplicateError("Esta huella ya se encuentra registrada en el sistema.")
            templates.append(template)
            if len(templates) < self.enroll_samples:
                self._wait_for_finger_release(device)
        return templates

    def _capture_template(self, device):
        deadline = monotonic() + self.capture_timeout_seconds
        while monotonic() < deadline:
            capture = self._call(device, "AcquireFingerprint")
            if capture:
                template = capture[0] if isinstance(capture, tuple) else capture
                if template:
                    self._log("MESSAGE_CAPTURED_OK")
                    self._log("Template recibido")
                    return bytes(template)
            sleep(0.2)
        raise FingerprintDeviceError("Tiempo agotado esperando huella en el lector ZK9500.")

    def _wait_for_finger_release(self, device):
        deadline = monotonic() + self.release_timeout_seconds
        while monotonic() < deadline:
            capture = self._call(device, "AcquireFingerprint")
            if not capture:
                return
            sleep(0.2)
        raise FingerprintDeviceError("Retire el dedo del lector antes de continuar con la siguiente captura.")

    def _validate_same_finger(self, device, templates):
        if len(templates) < 2:
            return
        reference = templates[0]
        for template in templates[1:]:
            if self._match(device, reference, template) < self.match_threshold:
                raise FingerprintDeviceError(
                    "Las muestras capturadas no corresponden a la misma huella."
                )

    def _merge_templates(self, device, templates):
        if len(templates) < 3:
            raise FingerprintDeviceError("ZKFinger requiere tres muestras para registrar una huella.")

        result = self._call(device, "DBMerge", templates[0], templates[1], templates[2])
        if isinstance(result, tuple):
            merged_template = result[0]
        else:
            merged_template = result

        if not merged_template:
            raise FingerprintDeviceError("No se pudo fusionar el template biometrico.")
        return bytes(merged_template)

    def _identify_with_database(self, device, captured_template, fingerprints):
        fingerprints_by_id = self._load_fingerprints_into_database(device, fingerprints)
        identified = self._call(device, "DBIdentify", captured_template)
        finger_id = None
        score = 0
        if isinstance(identified, tuple):
            finger_id = identified[0]
            score = identified[1] if len(identified) > 1 else self.match_threshold
        elif isinstance(identified, int):
            finger_id = identified
            score = self.match_threshold

        if finger_id in fingerprints_by_id and score >= self.match_threshold:
            return fingerprints_by_id[finger_id]

        return self._identify_by_matching(device, captured_template, fingerprints)

    def _load_fingerprints_into_database(self, device, fingerprints):
        self._call_if_exists(device, "DBClear")
        fingerprints_by_id = {}
        for fingerprint in fingerprints:
            add_result = self._call(device, "DBAdd", fingerprint.id, fingerprint.template_biometrico)
            if add_result not in (None, 0):
                continue
            fingerprints_by_id[fingerprint.id] = fingerprint
        return fingerprints_by_id

    def _identify_loaded_template(self, device, template):
        identified = self._call(device, "DBIdentify", template)
        if isinstance(identified, tuple):
            finger_id = identified[0]
            score = identified[1] if len(identified) > 1 else self.match_threshold
            return finger_id if finger_id and score >= self.match_threshold else None
        if isinstance(identified, int):
            return identified if identified > 0 else None
        return None

    def _identify_by_matching(self, device, captured_template, fingerprints):
        best_fingerprint = None
        best_score = -1
        for fingerprint in fingerprints:
            score = self._match(device, captured_template, fingerprint.template_biometrico)
            if score > best_score:
                best_score = score
                best_fingerprint = fingerprint
        if best_score >= self.match_threshold:
            return best_fingerprint
        return None

    def _match(self, device, template_a, template_b):
        result = self._call(device, "DBMatch", template_a, template_b)
        if isinstance(result, bool):
            return 1 if result else 0
        return int(result or 0)

    def _terminate_device(self, device):
        if not device:
            return
        for method_name in ("DBFree", "CloseDevice", "Terminate"):
            try:
                self._call_if_exists(device, method_name)
            except Exception:
                continue

    def _call(self, device, method_name, *args):
        method = getattr(device, method_name, None)
        if not method:
            raise FingerprintDeviceError(f"El SDK no expone {method_name}.")
        return method(*args)

    def _call_if_exists(self, device, method_name, *args):
        method = getattr(device, method_name, None)
        if method:
            return method(*args)
        return None

    def _log(self, message):
        self.logger.info("[BIOMETRIC] %s", message)
        print(f"[BIOMETRIC] {message}", flush=True)
