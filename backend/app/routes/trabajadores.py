from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_

from app import db
from app.models import Auditoria, Huella, HorarioTrabajador, Trabajador
from app.routes.auth import current_admin, require_admin
from app.services.fingerprint import get_fingerprint_provider
from app.services.fingerprint.real_provider import FingerprintDeviceError, FingerprintDuplicateError

trabajadores_bp = Blueprint("trabajadores", __name__)


def serialize_time(value):
    return value.strftime("%H:%M") if value else None


def serialize_current_schedule(schedule):
    if not schedule:
        return None
    return {
        "id": schedule.id,
        "plantilla_id": schedule.plantilla_id,
        "hora_entrada": serialize_time(schedule.hora_entrada),
        "hora_salida_almuerzo": serialize_time(schedule.hora_salida_almuerzo),
        "hora_regreso_almuerzo": serialize_time(schedule.hora_regreso_almuerzo),
        "hora_salida": serialize_time(schedule.hora_salida),
        "fecha_inicio": schedule.fecha_inicio.isoformat(),
        "fecha_fin": schedule.fecha_fin.isoformat() if schedule.fecha_fin else None,
        "activo": schedule.activo,
    }


def get_current_schedule(trabajador_id):
    return (
        HorarioTrabajador.query.filter_by(trabajador_id=trabajador_id, activo=True)
        .order_by(HorarioTrabajador.fecha_inicio.desc(), HorarioTrabajador.id.desc())
        .first()
    )


def has_active_fingerprint(trabajador_id):
    return (
        db.session.query(Huella.id)
        .filter_by(trabajador_id=trabajador_id, activa=True)
        .first()
        is not None
    )


def serialize_worker(worker):
    schedule = get_current_schedule(worker.id)
    return {
        "id": worker.id,
        "codigo": worker.codigo,
        "nombre": worker.nombre,
        "apellido": worker.apellido,
        "activo": worker.activo,
        "estado": "Activo" if worker.activo else "Inactivo",
        "horario": serialize_current_schedule(schedule),
        "estado_huella": "Registrada" if has_active_fingerprint(worker.id) else "Pendiente",
        "created_at": worker.created_at.isoformat() if worker.created_at else None,
        "updated_at": worker.updated_at.isoformat() if worker.updated_at else None,
    }


def next_worker_code():
    """
    Genera el siguiente codigo EMP-0001 para nuevos trabajadores.

    Recibe:
        No recibe parametros.

    Utilizado desde:
        POST /api/admin/trabajadores

    Retorna:
        Codigo automatico disponible.
    """
    last_code = (
        db.session.query(Trabajador.codigo)
        .filter(Trabajador.codigo.like("EMP-%"))
        .order_by(Trabajador.codigo.desc())
        .first()
    )
    if not last_code:
        return "EMP-0001"

    try:
        next_number = int(last_code[0].split("-")[1]) + 1
    except (IndexError, ValueError):
        next_number = (db.session.query(func.count(Trabajador.id)).scalar() or 0) + 1
    return f"EMP-{next_number:04d}"


def validate_worker_payload(data):
    nombre = (data.get("nombre") or "").strip()
    apellido = (data.get("apellido") or "").strip()

    errors = {}
    if not nombre:
        errors["nombre"] = "El nombre es obligatorio."
    if not apellido:
        errors["apellido"] = "El apellido es obligatorio."

    return nombre, apellido, errors


def audit(action, entity_id, description):
    admin = current_admin()
    db.session.add(
        Auditoria(
            administrador_id=admin.id if admin else None,
            accion=action,
            entidad="trabajadores",
            entidad_id=entity_id,
            descripcion=description,
            ip=request.remote_addr,
        )
    )


@trabajadores_bp.get("")
@require_admin
def list_workers():
    query = Trabajador.query
    search = (request.args.get("q") or "").strip()
    estado = (request.args.get("estado") or "").strip()

    if search:
        like_search = f"%{search}%"
        query = query.filter(
            or_(
                Trabajador.codigo.like(like_search),
                Trabajador.nombre.like(like_search),
                Trabajador.apellido.like(like_search),
            )
        )
    if estado == "activo":
        query = query.filter_by(activo=True)
    elif estado == "inactivo":
        query = query.filter_by(activo=False)

    workers = query.order_by(Trabajador.codigo.asc()).all()
    return jsonify({"success": True, "data": {"trabajadores": [serialize_worker(w) for w in workers]}})


@trabajadores_bp.post("")
@require_admin
def create_worker():
    data = request.get_json(silent=True) or {}
    nombre, apellido, errors = validate_worker_payload(data)
    if errors:
        return jsonify({"success": False, "code": "DATOS_INVALIDOS", "errors": errors}), 400

    code = (data.get("codigo") or "").strip().upper() or next_worker_code()
    if Trabajador.query.filter_by(codigo=code).first():
        return (
            jsonify(
                {
                    "success": False,
                    "code": "CODIGO_DUPLICADO",
                    "message": "Ya existe un trabajador con ese codigo.",
                }
            ),
            409,
        )

    provider = get_fingerprint_provider()
    fingerprint_id = (data.get("fingerprint_id") or "").strip().upper()
    enroll_fingerprint = bool(data.get("enroll_fingerprint"))
    requires_fingerprint = provider.provider_name != "mock"

    if requires_fingerprint and not enroll_fingerprint:
        return (
            jsonify(
                {
                    "success": False,
                    "code": "HUELLA_REQUERIDA",
                    "message": "Debe registrar una huella antes de crear un trabajador activo.",
                }
            ),
            400,
        )

    template = None
    if enroll_fingerprint:
        try:
            active_fingerprints = Huella.query.filter_by(activa=True).all()
            template = provider.enroll(fingerprint_id, active_fingerprints=active_fingerprints)
        except ValueError as error:
            return (
                jsonify(
                    {
                        "success": False,
                        "code": "HUELLA_INVALIDA",
                        "message": str(error),
                    }
                ),
                400,
            )
        except FingerprintDeviceError as error:
            return (
                jsonify(
                    {
                        "success": False,
                        "code": "LECTOR_NO_DISPONIBLE",
                        "message": str(error),
                    }
                ),
                503,
            )
        except FingerprintDuplicateError as error:
            return (
                jsonify(
                    {
                        "success": False,
                        "code": "HUELLA_DUPLICADA",
                        "message": str(error),
                    }
                ),
                409,
            )

    worker = Trabajador(
        codigo=code,
        nombre=nombre,
        apellido=apellido,
        activo=bool(template) or not requires_fingerprint,
    )
    db.session.add(worker)
    db.session.flush()
    if template:
        db.session.add(
            Huella(
                trabajador_id=worker.id,
                template_biometrico=template,
                proveedor=provider.provider_name,
                version=provider.version,
                activa=True,
            )
        )
    audit("CREAR_TRABAJADOR", worker.id, f"Trabajador creado: {worker.codigo}")
    db.session.commit()

    return (
        jsonify(
            {
                "success": True,
                "message": (
                    "Trabajador creado con huella registrada correctamente."
                    if template
                    else "Trabajador creado correctamente."
                ),
                "data": {"trabajador": serialize_worker(worker)},
            }
        ),
        201,
    )


@trabajadores_bp.get("/<int:worker_id>")
@require_admin
def get_worker(worker_id):
    worker = Trabajador.query.get_or_404(worker_id)
    return jsonify({"success": True, "data": {"trabajador": serialize_worker(worker)}})


@trabajadores_bp.put("/<int:worker_id>")
@require_admin
def update_worker(worker_id):
    worker = Trabajador.query.get_or_404(worker_id)
    data = request.get_json(silent=True) or {}
    nombre, apellido, errors = validate_worker_payload(data)
    if errors:
        return jsonify({"success": False, "code": "DATOS_INVALIDOS", "errors": errors}), 400

    code = (data.get("codigo") or worker.codigo).strip().upper()
    duplicated = Trabajador.query.filter(Trabajador.codigo == code, Trabajador.id != worker.id).first()
    if duplicated:
        return (
            jsonify(
                {
                    "success": False,
                    "code": "CODIGO_DUPLICADO",
                    "message": "Ya existe otro trabajador con ese codigo.",
                }
            ),
            409,
        )

    worker.codigo = code
    worker.nombre = nombre
    worker.apellido = apellido
    audit("EDITAR_TRABAJADOR", worker.id, f"Trabajador editado: {worker.codigo}")
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": "Trabajador actualizado correctamente.",
            "data": {"trabajador": serialize_worker(worker)},
        }
    )


@trabajadores_bp.patch("/<int:worker_id>/activar")
@require_admin
def activate_worker(worker_id):
    worker = Trabajador.query.get_or_404(worker_id)
    provider = get_fingerprint_provider()
    if provider.provider_name != "mock" and not has_active_fingerprint(worker.id):
        return (
            jsonify(
                {
                    "success": False,
                    "code": "HUELLA_REQUERIDA",
                    "message": "No puede activar un trabajador sin huella registrada.",
                }
            ),
            400,
        )
    worker.activo = True
    audit("ACTIVAR_TRABAJADOR", worker.id, f"Trabajador activado: {worker.codigo}")
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": "Trabajador activado correctamente.",
            "data": {"trabajador": serialize_worker(worker)},
        }
    )


@trabajadores_bp.patch("/<int:worker_id>/desactivar")
@require_admin
def deactivate_worker(worker_id):
    worker = Trabajador.query.get_or_404(worker_id)
    worker.activo = False
    audit("DESACTIVAR_TRABAJADOR", worker.id, f"Trabajador desactivado: {worker.codigo}")
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": "Trabajador desactivado correctamente.",
            "data": {"trabajador": serialize_worker(worker)},
        }
    )
