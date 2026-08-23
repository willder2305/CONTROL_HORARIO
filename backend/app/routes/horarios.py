from flask import Blueprint, jsonify, request

from app import db
from app.models import Auditoria, HorarioTrabajador, PlantillaHorario, Trabajador
from app.routes.auth import current_admin, require_admin
from app.services.schedule_service import (
    assign_worker_schedule,
    build_template_payload,
    schedule_payload_from_assignment,
    serialize_template,
    serialize_worker_schedule,
)

horarios_bp = Blueprint("horarios", __name__)


def audit(action, entity, entity_id, description):
    admin = current_admin()
    db.session.add(
        Auditoria(
            administrador_id=admin.id if admin else None,
            accion=action,
            entidad=entity,
            entidad_id=entity_id,
            descripcion=description,
            ip=request.remote_addr,
        )
    )


@horarios_bp.get("/plantillas")
@require_admin
def list_templates():
    templates = PlantillaHorario.query.order_by(
        PlantillaHorario.activo.desc(),
        PlantillaHorario.nombre.asc(),
    ).all()
    return jsonify(
        {"success": True, "data": {"plantillas": [serialize_template(t) for t in templates]}}
    )


@horarios_bp.post("/plantillas")
@require_admin
def create_template():
    data = request.get_json(silent=True) or {}
    payload, errors = build_template_payload(data)
    if errors:
        return jsonify({"success": False, "code": "DATOS_INVALIDOS", "errors": errors}), 400

    if PlantillaHorario.query.filter_by(nombre=payload["nombre"]).first():
        return (
            jsonify(
                {
                    "success": False,
                    "code": "PLANTILLA_DUPLICADA",
                    "message": "Ya existe una plantilla con ese nombre.",
                }
            ),
            409,
        )

    template = PlantillaHorario(**payload, activo=True)
    db.session.add(template)
    db.session.flush()
    audit("CREAR_PLANTILLA_HORARIO", "plantillas_horario", template.id, template.nombre)
    db.session.commit()
    return (
        jsonify(
            {
                "success": True,
                "message": "Plantilla creada correctamente.",
                "data": {"plantilla": serialize_template(template)},
            }
        ),
        201,
    )


@horarios_bp.put("/plantillas/<int:template_id>")
@require_admin
def update_template(template_id):
    template = PlantillaHorario.query.get_or_404(template_id)
    data = request.get_json(silent=True) or {}
    payload, errors = build_template_payload(data)
    if errors:
        return jsonify({"success": False, "code": "DATOS_INVALIDOS", "errors": errors}), 400

    duplicated = PlantillaHorario.query.filter(
        PlantillaHorario.nombre == payload["nombre"],
        PlantillaHorario.id != template.id,
    ).first()
    if duplicated:
        return (
            jsonify(
                {
                    "success": False,
                    "code": "PLANTILLA_DUPLICADA",
                    "message": "Ya existe otra plantilla con ese nombre.",
                }
            ),
            409,
        )

    for field, value in payload.items():
        setattr(template, field, value)
    audit("EDITAR_PLANTILLA_HORARIO", "plantillas_horario", template.id, template.nombre)
    db.session.commit()
    return jsonify(
        {
            "success": True,
            "message": "Plantilla actualizada correctamente.",
            "data": {"plantilla": serialize_template(template)},
        }
    )


@horarios_bp.patch("/plantillas/<int:template_id>/desactivar")
@require_admin
def deactivate_template(template_id):
    template = PlantillaHorario.query.get_or_404(template_id)
    template.activo = False
    audit("DESACTIVAR_PLANTILLA_HORARIO", "plantillas_horario", template.id, template.nombre)
    db.session.commit()
    return jsonify(
        {
            "success": True,
            "message": "Plantilla desactivada correctamente.",
            "data": {"plantilla": serialize_template(template)},
        }
    )


@horarios_bp.post("/trabajadores/<int:worker_id>/asignar")
@require_admin
def assign_schedule(worker_id):
    worker = Trabajador.query.get_or_404(worker_id)
    data = request.get_json(silent=True) or {}
    payload, errors = schedule_payload_from_assignment(data)
    if errors:
        return jsonify({"success": False, "code": "DATOS_INVALIDOS", "errors": errors}), 400

    had_active_schedule = (
        HorarioTrabajador.query.filter_by(trabajador_id=worker.id, activo=True).first()
        is not None
    )
    schedule = assign_worker_schedule(worker.id, payload)
    db.session.flush()
    action = "MODIFICAR_HORARIO" if had_active_schedule else "ASIGNAR_HORARIO"
    audit(
        action,
        "horarios_trabajadores",
        schedule.id,
        f"Horario {'modificado' if had_active_schedule else 'asignado'} a {worker.codigo}",
    )
    db.session.commit()
    return (
        jsonify(
            {
                "success": True,
                "message": "Horario asignado correctamente.",
                "data": {"horario": serialize_worker_schedule(schedule)},
            }
        ),
        201,
    )


@horarios_bp.get("/trabajadores/<int:worker_id>/actual")
@require_admin
def current_worker_schedule(worker_id):
    Trabajador.query.get_or_404(worker_id)
    schedule = (
        HorarioTrabajador.query.filter_by(trabajador_id=worker_id, activo=True)
        .order_by(HorarioTrabajador.fecha_inicio.desc(), HorarioTrabajador.id.desc())
        .first()
    )
    return jsonify(
        {
            "success": True,
            "data": {"horario": serialize_worker_schedule(schedule) if schedule else None},
        }
    )


@horarios_bp.get("/trabajadores/<int:worker_id>/historial")
@require_admin
def worker_schedule_history(worker_id):
    Trabajador.query.get_or_404(worker_id)
    schedules = (
        HorarioTrabajador.query.filter_by(trabajador_id=worker_id)
        .order_by(HorarioTrabajador.fecha_inicio.desc(), HorarioTrabajador.id.desc())
        .all()
    )
    return jsonify(
        {
            "success": True,
            "data": {"historial": [serialize_worker_schedule(schedule) for schedule in schedules]},
        }
    )
