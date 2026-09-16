"""Modulo health del sistema de control de horarios.

Agrupa la logica propia necesaria para esta responsabilidad sin exponer detalles de infraestructura.
"""

from flask import Blueprint, jsonify

from app.utils.datetime_utils import obtener_hora_actual

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    """
    Expone una comprobacion liviana de disponibilidad del backend.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    return jsonify({"status": "ok"})


@health_bp.get("/time")
def current_server_time():
    """
    Expone la hora oficial del servidor en la zona horaria operativa.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    return jsonify(
        {
            "timezone": "America/Guatemala",
            "fecha_hora": obtener_hora_actual().isoformat(),
        }
    )
