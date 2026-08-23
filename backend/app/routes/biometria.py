from flask import Blueprint, jsonify, request

from app import db
from app.models import Auditoria, Huella, Trabajador
from app.routes.auth import current_admin, require_admin
from app.services.fingerprint.real_provider import FingerprintDeviceError, FingerprintDuplicateError
from app.services.fingerprint import get_fingerprint_provider

biometria_bp = Blueprint("biometria", __name__)


def serialize_worker(worker):
    return {
        "id": worker.id,
        "codigo": worker.codigo,
        "nombre": worker.nombre,
        "apellido": worker.apellido,
        "activo": worker.activo,
    }


def serialize_fingerprint(fingerprint):
    return {
        "id": fingerprint.id,
        "trabajador_id": fingerprint.trabajador_id,
        "proveedor": fingerprint.proveedor,
        "version": fingerprint.version,
        "activa": fingerprint.activa,
        "created_at": fingerprint.created_at.isoformat() if fingerprint.created_at else None,
        "updated_at": fingerprint.updated_at.isoformat() if fingerprint.updated_at else None,
    }


def audit(action, entity_id, description):
    admin = current_admin()
    db.session.add(
        Auditoria(
            administrador_id=admin.id if admin else None,
            accion=action,
            entidad="huellas",
            entidad_id=entity_id,
            descripcion=description,
            ip=request.remote_addr,
        )
    )


@biometria_bp.post("/trabajadores/<int:worker_id>/registrar")
@require_admin
def enroll_worker_fingerprint(worker_id):
    worker = Trabajador.query.get_or_404(worker_id)
    data = request.get_json(silent=True) or {}
    fingerprint_id = (data.get("fingerprint_id") or "").strip().upper()
    provider = get_fingerprint_provider()

    try:
        active_fingerprints = (
            Huella.query.filter_by(activa=True)
            .filter(Huella.trabajador_id != worker.id)
            .all()
        )
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

    active_fingerprints = Huella.query.filter_by(trabajador_id=worker.id, activa=True).all()
    action = "REGISTRAR_HUELLA" if not active_fingerprints else "REEMPLAZAR_HUELLA"
    for fingerprint in active_fingerprints:
        fingerprint.activa = False

    fingerprint = Huella(
        trabajador_id=worker.id,
        template_biometrico=template,
        proveedor=provider.provider_name,
        version=provider.version,
        activa=True,
    )
    db.session.add(fingerprint)
    db.session.flush()
    audit(action, fingerprint.id, f"{action} para trabajador {worker.codigo}")
    db.session.commit()

    return (
        jsonify(
            {
                "success": True,
                "message": "Huella registrada correctamente.",
                "data": {
                    "trabajador": serialize_worker(worker),
                    "huella": serialize_fingerprint(fingerprint),
                },
            }
        ),
        201,
    )


@biometria_bp.get("/device/status")
@require_admin
def device_status():
    provider = get_fingerprint_provider()
    return jsonify({"success": True, "data": provider.status()})


@biometria_bp.get("/trabajadores/<int:worker_id>/estado")
@require_admin
def worker_fingerprint_status(worker_id):
    worker = Trabajador.query.get_or_404(worker_id)
    fingerprint = Huella.query.filter_by(trabajador_id=worker.id, activa=True).first()
    return jsonify(
        {
            "success": True,
            "data": {
                "trabajador": serialize_worker(worker),
                "huella": serialize_fingerprint(fingerprint) if fingerprint else None,
                "estado_huella": "Registrada" if fingerprint else "Pendiente",
            },
        }
    )


@biometria_bp.post("/identificar")
def identify_fingerprint():
    data = request.get_json(silent=True) or {}
    fingerprint_id = (data.get("fingerprint_id") or "").strip().upper()
    provider = get_fingerprint_provider()
    active_fingerprints = Huella.query.filter_by(activa=True).all()

    try:
        fingerprint = provider.identify(fingerprint_id, active_fingerprints)
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

    if not fingerprint or not fingerprint.trabajador:
        return (
            jsonify(
                {
                    "success": False,
                    "code": "HUELLA_NO_RECONOCIDA",
                    "message": "Huella no reconocida.",
                }
            ),
            404,
        )

    if not fingerprint.trabajador.activo:
        return (
            jsonify(
                {
                    "success": False,
                    "code": "TRABAJADOR_INACTIVO",
                    "message": "El trabajador identificado esta inactivo.",
                }
            ),
            403,
        )

    return jsonify(
        {
            "success": True,
            "message": "Trabajador identificado correctamente.",
            "data": {"trabajador": serialize_worker(fingerprint.trabajador)},
        }
    )
