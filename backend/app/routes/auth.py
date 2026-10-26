"""Modulo auth del sistema de control de horarios.

Agrupa la logica propia necesaria para esta responsabilidad sin exponer detalles de infraestructura.
"""

from functools import wraps

from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.security import check_password_hash

from app import db
from app.models import Administrador
from app.security import current_csrf_token, generate_csrf_token
from app.utils.datetime_utils import obtener_hora_actual

auth_bp = Blueprint("auth", __name__)


def session_expiration():
    """Calcula el vencimiento real de la sesion en la zona horaria operativa."""
    lifetime = current_app.permanent_session_lifetime
    if not isinstance(lifetime, timedelta):
        lifetime = timedelta(seconds=lifetime)
    return obtener_hora_actual() + lifetime


def refresh_session_expiration():
    """Renueva el vencimiento de una sesion autenticada sin cambiar al administrador."""
    expires_at = session_expiration()
    session.permanent = True
    session["expires_at"] = expires_at.isoformat()
    session.modified = True
    return expires_at


def remaining_session_seconds():
    """Devuelve los segundos restantes de sesion o ``None`` para sesiones heredadas."""
    raw_expiration = session.get("expires_at")
    if not raw_expiration:
        return None
    try:
        expires_at = datetime.fromisoformat(raw_expiration)
    except (TypeError, ValueError):
        return 0
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=obtener_hora_actual().tzinfo)
    return max(0, int((expires_at - obtener_hora_actual()).total_seconds()))


def serialize_admin(admin):
    """
    Atiende el endpoint Flask asociado a serialize_admin y devuelve una respuesta JSON acorde al resultado de la operacion.

    Args:
        admin: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    return {
        "id": admin.id,
        "usuario": admin.usuario,
        "nombre": admin.nombre,
        "apellido": admin.apellido,
        "activo": admin.activo,
    }


def current_admin():
    """
    Atiende el endpoint Flask asociado a current_admin y devuelve una respuesta JSON acorde al resultado de la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    admin_id = session.get("admin_id")
    if not admin_id:
        return None
    seconds_remaining = remaining_session_seconds()
    if seconds_remaining == 0:
        session.clear()
        return None
    return Administrador.query.filter_by(id=admin_id, activo=True).first()


def require_admin(view):
    """
    Protege endpoints administrativos validando la sesion Flask activa.

    Recibe:
        Funcion de vista Flask.

    Utilizado desde:
        Rutas bajo /api/admin agregadas en fases posteriores.

    Retorna:
        La vista original si hay sesion; error 401 si no existe sesion valida.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        """
        Atiende el endpoint Flask asociado a wrapped y devuelve una respuesta JSON acorde al resultado de la operacion.

        Returns:
            Resultado de la operacion o respuesta HTTP correspondiente.
        """
        admin = current_admin()
        if not admin:
            return (
                jsonify(
                    {
                        "success": False,
                        "code": "NO_AUTENTICADO",
                        "message": "Debe iniciar sesión como administrador.",
                    }
                ),
                401,
            )
        return view(*args, **kwargs)

    return wrapped


@auth_bp.post("/login")
def login():
    """
    Atiende el endpoint Flask asociado a login y devuelve una respuesta JSON acorde al resultado de la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    data = request.get_json(silent=True) or {}
    usuario = (data.get("usuario") or "").strip()
    password = data.get("password") or ""

    if not usuario or not password:
        return (
            jsonify(
                {
                    "success": False,
                    "code": "CREDENCIALES_REQUERIDAS",
                    "message": "Usuario y contraseña son obligatorios.",
                }
            ),
            400,
        )

    # MySQL often uses a case-insensitive collation.  Keep the database query
    # indexed, then require an exact Python comparison before authenticating.
    candidates = Administrador.query.filter(Administrador.usuario == usuario).all()
    admin = next((candidate for candidate in candidates if candidate.usuario == usuario), None)
    if not admin or not admin.activo or not check_password_hash(admin.password_hash, password):
        return (
            jsonify(
                {
                    "success": False,
                    "code": "CREDENCIALES_INVALIDAS",
                    "message": "Usuario o contraseña incorrectos.",
                }
            ),
            401,
        )

    session.clear()
    session.permanent = True
    session["admin_id"] = admin.id
    session["admin_usuario"] = admin.usuario
    expires_at = refresh_session_expiration()
    csrf_token = generate_csrf_token()

    admin.ultimo_login = obtener_hora_actual()
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": "Inicio de sesión correcto.",
            "data": {
                "admin": serialize_admin(admin),
                "csrf_token": csrf_token,
                "expires_at": expires_at.isoformat(),
            },
        }
    )


@auth_bp.post("/logout")
def logout():
    """
    Atiende el endpoint Flask asociado a logout y devuelve una respuesta JSON acorde al resultado de la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    session.clear()
    return jsonify({"success": True, "message": "Sesión cerrada correctamente."})


@auth_bp.get("/me")
def me():
    """
    Atiende el endpoint Flask asociado a me y devuelve una respuesta JSON acorde al resultado de la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    admin = current_admin()
    if not admin:
        return (
            jsonify(
                {
                    "success": False,
                    "code": "NO_AUTENTICADO",
                    "message": "No hay sesión activa.",
                }
            ),
            401,
        )
    return jsonify(
        {
            "success": True,
            "data": {
                "admin": serialize_admin(admin),
                "csrf_token": current_csrf_token(),
                "expires_at": session.get("expires_at"),
            },
        }
    )


@auth_bp.get("/session")
@require_admin
def session_status():
    """Expone solo el vencimiento de la sesion para que el cliente avise a tiempo."""
    seconds_remaining = remaining_session_seconds()
    if seconds_remaining is None:
        expires_at = refresh_session_expiration()
        seconds_remaining = max(0, int((expires_at - obtener_hora_actual()).total_seconds()))
    return jsonify(
        {
            "success": True,
            "data": {
                "authenticated": True,
                "expires_at": session.get("expires_at"),
                "seconds_remaining": seconds_remaining,
            },
        }
    )


@auth_bp.post("/session/refresh")
@require_admin
def refresh_session():
    """Renueva una sesion autenticada de forma explicita y protegida por CSRF."""
    expires_at = refresh_session_expiration()
    return jsonify(
        {
            "success": True,
            "message": "Sesión extendida correctamente.",
            "data": {
                "expires_at": expires_at.isoformat(),
                "seconds_remaining": max(
                    0, int((expires_at - obtener_hora_actual()).total_seconds())
                ),
            },
        }
    )
