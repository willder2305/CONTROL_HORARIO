import base64
import binascii

from app.models import Huella
from app.services.fingerprint.real_provider import FingerprintDuplicateError


def encode_template_b64(template):
    return base64.b64encode(template).decode("ascii")


def decode_template_b64(template_biometrico):
    raw_value = (template_biometrico or "").strip()
    if not raw_value:
        raise ValueError("El template biometrico es obligatorio.")
    if "," in raw_value and raw_value.lower().startswith("data:"):
        raw_value = raw_value.split(",", 1)[1]
    try:
        template = base64.b64decode(raw_value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("El template biometrico no tiene un formato valido.") from error
    if not template:
        raise ValueError("El template biometrico esta vacio.")
    return template


def ensure_template_is_unique(template, excluded_worker_id=None):
    query = Huella.query.filter_by(activa=True)
    if excluded_worker_id is not None:
        query = query.filter(Huella.trabajador_id != excluded_worker_id)
    for fingerprint in query.all():
        if fingerprint.template_biometrico == template:
            raise FingerprintDuplicateError("Esta huella ya se encuentra registrada en el sistema.")


def template_from_agent_payload(data, excluded_worker_id=None):
    value = data.get("template_biometrico") or data.get("templateBiometrico")
    if not value:
        return None
    template = decode_template_b64(value)
    ensure_template_is_unique(template, excluded_worker_id=excluded_worker_id)
    return template
