from datetime import datetime, timedelta

from app import db
from app.models import HorarioTrabajador, PlantillaHorario


def parse_time(value, field_name, errors):
    if not value:
        errors[field_name] = "Campo obligatorio."
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        errors[field_name] = "Formato invalido. Use HH:MM."
        return None


def parse_optional_time(value, field_name, errors):
    if not value:
        return None
    return parse_time(value, field_name, errors)


def parse_date(value, field_name, errors):
    if not value:
        errors[field_name] = "Campo obligatorio."
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        errors[field_name] = "Formato invalido. Use YYYY-MM-DD."
        return None


def serialize_time(value):
    return value.strftime("%H:%M") if value else None


def serialize_date(value):
    return value.isoformat() if value else None


def serialize_template(template):
    return {
        "id": template.id,
        "nombre": template.nombre,
        "hora_entrada": serialize_time(template.hora_entrada),
        "hora_salida_almuerzo": serialize_time(template.hora_salida_almuerzo),
        "hora_regreso_almuerzo": serialize_time(template.hora_regreso_almuerzo),
        "hora_salida": serialize_time(template.hora_salida),
        "tolerancia_entrada": template.tolerancia_entrada,
        "tolerancia_regreso_almuerzo": template.tolerancia_regreso_almuerzo,
        "activo": template.activo,
    }


def serialize_worker_schedule(schedule):
    template_name = schedule.plantilla.nombre if schedule.plantilla else None
    return {
        "id": schedule.id,
        "trabajador_id": schedule.trabajador_id,
        "plantilla_id": schedule.plantilla_id,
        "plantilla_nombre": template_name,
        "hora_entrada": serialize_time(schedule.hora_entrada),
        "hora_salida_almuerzo": serialize_time(schedule.hora_salida_almuerzo),
        "hora_regreso_almuerzo": serialize_time(schedule.hora_regreso_almuerzo),
        "hora_salida": serialize_time(schedule.hora_salida),
        "tolerancia_entrada": schedule.tolerancia_entrada,
        "tolerancia_regreso_almuerzo": schedule.tolerancia_regreso_almuerzo,
        "fecha_inicio": serialize_date(schedule.fecha_inicio),
        "fecha_fin": serialize_date(schedule.fecha_fin),
        "activo": schedule.activo,
    }


def build_template_payload(data):
    """
    Valida y normaliza los campos de una plantilla de horario.

    Recibe:
        Diccionario JSON del frontend.

    Utilizado desde:
        Rutas de administracion de horarios.

    Retorna:
        Tupla (payload, errors).
    """
    errors = {}
    payload = {
        "nombre": (data.get("nombre") or "").strip().upper(),
        "hora_entrada": parse_time(data.get("hora_entrada"), "hora_entrada", errors),
        "hora_salida_almuerzo": parse_optional_time(
            data.get("hora_salida_almuerzo"),
            "hora_salida_almuerzo",
            errors,
        ),
        "hora_regreso_almuerzo": parse_optional_time(
            data.get("hora_regreso_almuerzo"),
            "hora_regreso_almuerzo",
            errors,
        ),
        "hora_salida": parse_time(data.get("hora_salida"), "hora_salida", errors),
        "tolerancia_entrada": int(data.get("tolerancia_entrada") or 0),
        "tolerancia_regreso_almuerzo": int(
            data.get("tolerancia_regreso_almuerzo") or 0
        ),
    }
    if not payload["nombre"]:
        errors["nombre"] = "El nombre es obligatorio."
    if payload["tolerancia_entrada"] < 0:
        errors["tolerancia_entrada"] = "No puede ser negativa."
    if payload["tolerancia_regreso_almuerzo"] < 0:
        errors["tolerancia_regreso_almuerzo"] = "No puede ser negativa."
    if bool(payload["hora_salida_almuerzo"]) != bool(payload["hora_regreso_almuerzo"]):
        errors["almuerzo"] = "Configure ambas horas de almuerzo o deje ambas vacias."
    return payload, errors


def schedule_payload_from_assignment(data):
    errors = {}
    plantilla_id = data.get("plantilla_id") or None
    template = None

    if plantilla_id:
        template = PlantillaHorario.query.filter_by(id=plantilla_id, activo=True).first()
        if not template:
            errors["plantilla_id"] = "Plantilla no encontrada o inactiva."

    fecha_inicio = parse_date(data.get("fecha_inicio"), "fecha_inicio", errors)

    if template:
        payload = {
            "plantilla_id": template.id,
            "hora_entrada": template.hora_entrada,
            "hora_salida_almuerzo": template.hora_salida_almuerzo,
            "hora_regreso_almuerzo": template.hora_regreso_almuerzo,
            "hora_salida": template.hora_salida,
            "tolerancia_entrada": template.tolerancia_entrada,
            "tolerancia_regreso_almuerzo": template.tolerancia_regreso_almuerzo,
            "fecha_inicio": fecha_inicio,
        }
    else:
        payload = {
            "plantilla_id": None,
            "hora_entrada": parse_time(data.get("hora_entrada"), "hora_entrada", errors),
            "hora_salida_almuerzo": parse_optional_time(
                data.get("hora_salida_almuerzo"),
                "hora_salida_almuerzo",
                errors,
            ),
            "hora_regreso_almuerzo": parse_optional_time(
                data.get("hora_regreso_almuerzo"),
                "hora_regreso_almuerzo",
                errors,
            ),
            "hora_salida": parse_time(data.get("hora_salida"), "hora_salida", errors),
            "tolerancia_entrada": int(data.get("tolerancia_entrada") or 0),
            "tolerancia_regreso_almuerzo": int(
                data.get("tolerancia_regreso_almuerzo") or 0
            ),
            "fecha_inicio": fecha_inicio,
        }

    if payload.get("tolerancia_entrada", 0) < 0:
        errors["tolerancia_entrada"] = "No puede ser negativa."
    if payload.get("tolerancia_regreso_almuerzo", 0) < 0:
        errors["tolerancia_regreso_almuerzo"] = "No puede ser negativa."
    if bool(payload.get("hora_salida_almuerzo")) != bool(payload.get("hora_regreso_almuerzo")):
        errors["almuerzo"] = "Configure ambas horas de almuerzo o deje ambas vacias."

    return payload, errors


def close_previous_active_schedule(trabajador_id, fecha_inicio):
    active_schedules = HorarioTrabajador.query.filter_by(
        trabajador_id=trabajador_id,
        activo=True,
    ).all()
    closing_date = fecha_inicio - timedelta(days=1)
    for schedule in active_schedules:
        schedule.fecha_fin = closing_date
        schedule.activo = False


def assign_worker_schedule(trabajador_id, payload):
    """
    Cierra horarios activos anteriores y crea una nueva asignacion vigente.

    Recibe:
        trabajador_id y payload validado de horario.

    Utilizado desde:
        POST /api/admin/horarios/trabajadores/<id>/asignar

    Retorna:
        HorarioTrabajador creado.
    """
    close_previous_active_schedule(trabajador_id, payload["fecha_inicio"])
    schedule = HorarioTrabajador(trabajador_id=trabajador_id, activo=True, **payload)
    db.session.add(schedule)
    return schedule
