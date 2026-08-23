from flask import Blueprint, jsonify

from app.utils.datetime_utils import obtener_hora_actual

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    return jsonify({"status": "ok"})


@health_bp.get("/time")
def current_server_time():
    return jsonify(
        {
            "timezone": "America/Guatemala",
            "fecha_hora": obtener_hora_actual().isoformat(),
        }
    )
