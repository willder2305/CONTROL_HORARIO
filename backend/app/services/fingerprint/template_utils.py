"""Modulo template utils del sistema de control de horarios.

Agrupa la logica propia necesaria para esta responsabilidad sin exponer detalles de infraestructura.
"""

import base64
import binascii

from app.models import Huella
from app.services.fingerprint.real_provider import FingerprintDuplicateError


def encode_template_b64(template):
    """
    Codifica un template binario en Base64 para el canal autenticado entre backend y agente local.

    Args:
        template: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    return base64.b64encode(template).decode("ascii")


def decode_template_b64(template_biometrico):
    """
    Valida y decodifica un template Base64 recibido desde el agente biometrico.

    Args:
        template_biometrico: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
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
    """
    Impide registrar un template biometrico que ya pertenezca a otra huella activa.

    Args:
        template: Dato utilizado por la operacion.
        excluded_worker_id: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    query = Huella.query.filter_by(activa=True)
    if excluded_worker_id is not None:
        query = query.filter(Huella.trabajador_id != excluded_worker_id)
    for fingerprint in query.all():
        if fingerprint.template_biometrico == template:
            raise FingerprintDuplicateError("Esta huella ya se encuentra registrada en el sistema.")


def template_from_agent_payload(data, excluded_worker_id=None):
    """
    Decodifica y valida el template enviado por el agente local antes de asociarlo a un trabajador.

    Args:
        data: Dato utilizado por la operacion.
        excluded_worker_id: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    value = data.get("template_biometrico") or data.get("templateBiometrico")
    if not value:
        return None
    template = decode_template_b64(value)
    ensure_template_is_unique(template, excluded_worker_id=excluded_worker_id)
    return template
