from functools import wraps

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash

from app import db
from app.models import Administrador
from app.security import current_csrf_token, generate_csrf_token
from app.utils.datetime_utils import obtener_hora_actual

auth_bp = Blueprint("auth", __name__)


def serialize_admin(admin):
    return {
        "id": admin.id,
        "usuario": admin.usuario,
        "nombre": admin.nombre,
        "apellido": admin.apellido,
        "activo": admin.activo,
    }


def current_admin():
    admin_id = session.get("admin_id")
    if not admin_id:
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
        admin = current_admin()
        if not admin:
            return (
                jsonify(
                    {
                        "success": False,
                        "code": "NO_AUTENTICADO",
                        "message": "Debe iniciar sesion como administrador.",
                    }
                ),
                401,
            )
        return view(*args, **kwargs)

    return wrapped


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    usuario = (data.get("usuario") or "").strip()
    password = data.get("password") or ""

    if not usuario or not password:
        return (
            jsonify(
                {
                    "success": False,
                    "code": "CREDENCIALES_REQUERIDAS",
                    "message": "Usuario y contrasena son obligatorios.",
                }
            ),
            400,
        )

    admin = Administrador.query.filter_by(usuario=usuario).first()
    if not admin or not admin.activo or not check_password_hash(admin.password_hash, password):
        return (
            jsonify(
                {
                    "success": False,
                    "code": "CREDENCIALES_INVALIDAS",
                    "message": "Usuario o contrasena incorrectos.",
                }
            ),
            401,
        )

    session.clear()
    session.permanent = True
    session["admin_id"] = admin.id
    session["admin_usuario"] = admin.usuario
    csrf_token = generate_csrf_token()

    admin.ultimo_login = obtener_hora_actual()
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": "Inicio de sesion correcto.",
            "data": {"admin": serialize_admin(admin), "csrf_token": csrf_token},
        }
    )


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Sesion cerrada correctamente."})


@auth_bp.get("/me")
def me():
    admin = current_admin()
    if not admin:
        return (
            jsonify(
                {
                    "success": False,
                    "code": "NO_AUTENTICADO",
                    "message": "No hay sesion activa.",
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
            },
        }
    )
