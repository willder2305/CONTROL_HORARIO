import hmac
from functools import wraps

from flask import Blueprint, current_app, jsonify, request

from app.models import Huella, Trabajador
from app.services.attendance_service import registrar_marcacion_por_huella_autorizada
from app.services.fingerprint.template_utils import encode_template_b64

agent_bp = Blueprint("agent", __name__)


def require_agent_token(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
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
    return jsonify({"success": True, "data": {"service": "agent-api", "ready": True}})


@agent_bp.get("/fingerprints")
@require_agent_token
def list_active_fingerprints():
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
