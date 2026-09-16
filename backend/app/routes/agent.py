"""Modulo agent del sistema de control de horarios.

Agrupa la logica propia necesaria para esta responsabilidad sin exponer detalles de infraestructura.
"""

import hmac
from functools import wraps

from flask import Blueprint, current_app, jsonify, request

from app.models import Huella, Trabajador
from app.services.attendance_service import registrar_marcacion_por_huella_autorizada
from app.services.fingerprint.template_utils import encode_template_b64

agent_bp = Blueprint("agent", __name__)


def require_agent_token(view):
    """
    Protege la comunicacion del agente local comparando su token mediante una operacion resistente a temporizacion.

    Args:
        view: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o configuracion registrada.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        """
        Atiende el endpoint Flask asociado a wrapped y devuelve una respuesta JSON acorde al resultado de la operacion.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        expected_token = current_app.config.get("BIOMETRIC_AGENT_TOKEN") or ""
        if not expected_token:
            return (
                jsonify(
                    {
                        "success": False,
                        "code": "AGENT_TOKEN_NO_CONFIGURADO",
                        "message": "Token de agente no configurado en el servidor.",
                    }
                ),
                503,
            )

        provided_token = request.headers.get("X-Agent-Token", "")
        if not hmac.compare_digest(provided_token, expected_token):
            return (
                jsonify(
                    {
                        "success": False,
                        "code": "AGENT_NO_AUTORIZADO",
                        "message": "Agente biometrico no autorizado.",
                    }
                ),
                401,
            )
        return view(*args, **kwargs)

    return wrapped


@agent_bp.get("/health")
@require_agent_token
def agent_health():
    """
    Expone el estado del canal protegido que utiliza ControlHorarioBiometricAgent.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    return jsonify({"success": True, "data": {"service": "agent-api", "ready": True}})


@agent_bp.get("/fingerprints")
@require_agent_token
def list_active_fingerprints():
    """
    Entrega al agente autenticado unicamente los templates activos necesarios para identificacion local.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    fingerprints = (
        Huella.query.join(Trabajador)
        .filter(Huella.activa.is_(True), Trabajador.activo.is_(True))
        .order_by(Huella.id.asc())
        .all()
    )
    payload = [
        {
            "id": fingerprint.id,
            "template": encode_template_b64(fingerprint.template_biometrico),
            "provider": fingerprint.proveedor,
            "version": fingerprint.version,
        }
        for fingerprint in fingerprints
    ]
    return jsonify(
        {
            "success": True,
            "data": {
                "fingerprints": payload,
                "count": len(payload),
            },
        }
    )


@agent_bp.post("/marcaciones")
@require_agent_token
def register_agent_mark():
    """
    Recibe una huella ya identificada por el agente local y delega la secuencia automatica de asistencia.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    data = request.get_json(silent=True) or {}
    try:
        fingerprint_id = int(data.get("huella_id") or data.get("fingerprint_id") or 0)
    except (TypeError, ValueError):
        fingerprint_id = 0

    if fingerprint_id <= 0:
        return (
            jsonify(
                {
                    "success": False,
                    "code": "HUELLA_INVALIDA",
                    "message": "Huella identificada invalida.",
                }
            ),
            400,
        )

    result = registrar_marcacion_por_huella_autorizada(fingerprint_id)
    if result["success"]:
        return jsonify(result), 201

    status_by_code = {
        "HUELLA_NO_RECONOCIDA": 404,
        "TRABAJADOR_INACTIVO": 403,
        "HORARIO_NO_ASIGNADO": 409,
        "JORNADA_COMPLETADA": 409,
        "MARCACION_RECIENTE": 429,
        "MARCACION_DUPLICADA": 409,
        "SECUENCIA_INVALIDA": 409,
    }
    return jsonify(result), status_by_code.get(result.get("code"), 400)
