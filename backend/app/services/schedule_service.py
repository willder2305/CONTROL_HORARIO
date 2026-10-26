"""Modulo schedule service del sistema de control de horarios.

Agrupa la logica propia necesaria para esta responsabilidad sin exponer detalles de infraestructura.
"""

from datetime import datetime, timedelta

from sqlalchemy import or_

from app import db
from app.models import HorarioTrabajador, PlantillaHorario


def parse_time(value, field_name, errors):
    """
    Valida y transforma datos externos al tipo de dominio esperado, informando errores de formato cuando corresponde.

    Args:
        value: Dato utilizado por la operacion.
        field_name: Dato utilizado por la operacion.
        errors: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    if not value:
        errors[field_name] = "Campo obligatorio."
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        errors[field_name] = "Formato invalido. Use HH:MM."
        return None


def parse_optional_time(value, field_name, errors):
    """
    Valida y transforma datos externos al tipo de dominio esperado, informando errores de formato cuando corresponde.

    Args:
        value: Dato utilizado por la operacion.
        field_name: Dato utilizado por la operacion.
        errors: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    if not value:
        return None
    return parse_time(value, field_name, errors)


def parse_non_negative_integer(value, field_name, errors):
    """Normaliza una tolerancia en minutos y rechaza texto, decimales o valores negativos."""
    if value in (None, ""):
        return 0
    if isinstance(value, bool) or (
        isinstance(value, float) and not value.is_integer()
    ):
        errors[field_name] = "Debe ser un numero entero igual o mayor que cero."
        return 0
    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        errors[field_name] = "Debe ser un numero entero igual o mayor que cero."
        return 0
    if parsed_value < 0:
        errors[field_name] = "No puede ser negativa."
        return 0
    return parsed_value


def parse_date(value, field_name, errors):
    """
    Valida y transforma datos externos al tipo de dominio esperado, informando errores de formato cuando corresponde.

    Args:
        value: Dato utilizado por la operacion.
        field_name: Dato utilizado por la operacion.
        errors: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    if not value:
        errors[field_name] = "Campo obligatorio."
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        errors[field_name] = "Formato invalido. Use YYYY-MM-DD."
        return None


def serialize_time(value):
    """
    Convierte una entidad de dominio a una estructura segura y serializable para respuestas de la API.

    Args:
        value: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    return value.strftime("%H:%M") if value else None


def serialize_date(value):
    """
    Convierte una entidad de dominio a una estructura segura y serializable para respuestas de la API.

    Args:
        value: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    return value.isoformat() if value else None


def serialize_template(template):
    """
    Convierte una entidad de dominio a una estructura segura y serializable para respuestas de la API.

    Args:
        template: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    return {
        "id": template.id,
        "nombre": template.nombre,
        "hora_entrada": serialize_time(template.hora_entrada),
        "hora_salida_almuerzo": serialize_time(template.hora_salida_almuerzo),
        "hora_regreso_almuerzo": serialize_time(template.hora_regreso_almuerzo),
        "hora_salida": serialize_time(template.hora_salida),
        "tolerancia_entrada": template.tolerancia_entrada,
        "tolerancia_salida": template.tolerancia_salida,
        "tolerancia_regreso_almuerzo": template.tolerancia_regreso_almuerzo,
        "activo": template.activo,
    }


def serialize_worker_schedule(schedule):
    """
    Convierte una entidad de dominio a una estructura segura y serializable para respuestas de la API.

    Args:
        schedule: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
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
        "tolerancia_salida": schedule.tolerancia_salida,
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
        "tolerancia_entrada": parse_non_negative_integer(
            data.get("tolerancia_entrada"), "tolerancia_entrada", errors
        ),
        "tolerancia_salida": parse_non_negative_integer(
            data.get("tolerancia_salida"), "tolerancia_salida", errors
        ),
        "tolerancia_regreso_almuerzo": parse_non_negative_integer(
            data.get("tolerancia_regreso_almuerzo"),
            "tolerancia_regreso_almuerzo",
            errors,
        ),
    }
    if not payload["nombre"]:
        errors["nombre"] = "El nombre es obligatorio."
    if bool(payload["hora_salida_almuerzo"]) != bool(payload["hora_regreso_almuerzo"]):
        errors["almuerzo"] = "Debe indicar la salida y el regreso de almuerzo."
    return payload, errors


def schedule_payload_from_assignment(data):
    """
    Implementa la responsabilidad de schedule payload from assignment dentro de este modulo.

    Args:
        data: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
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
            "tolerancia_salida": template.tolerancia_salida,
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
            "tolerancia_entrada": parse_non_negative_integer(
                data.get("tolerancia_entrada"), "tolerancia_entrada", errors
            ),
            "tolerancia_salida": parse_non_negative_integer(
                data.get("tolerancia_salida"), "tolerancia_salida", errors
            ),
            "tolerancia_regreso_almuerzo": parse_non_negative_integer(
                data.get("tolerancia_regreso_almuerzo"),
                "tolerancia_regreso_almuerzo",
                errors,
            ),
            "fecha_inicio": fecha_inicio,
        }

    if bool(payload.get("hora_salida_almuerzo")) != bool(payload.get("hora_regreso_almuerzo")):
        errors["almuerzo"] = "Debe indicar la salida y el regreso de almuerzo."

    return payload, errors


def _apply_schedule_payload(schedule, payload):
    for field, value in payload.items():
        if field != "fecha_inicio":
            setattr(schedule, field, value)


def _schedule_covering_date(trabajador_id, fecha):
    return (
        HorarioTrabajador.query.filter(
            HorarioTrabajador.trabajador_id == trabajador_id,
            HorarioTrabajador.fecha_inicio < fecha,
            or_(HorarioTrabajador.fecha_fin.is_(None), HorarioTrabajador.fecha_fin >= fecha),
        )
        .order_by(HorarioTrabajador.fecha_inicio.desc(), HorarioTrabajador.id.desc())
        .first()
    )


def _next_schedule(trabajador_id, fecha):
    return (
        HorarioTrabajador.query.filter(
            HorarioTrabajador.trabajador_id == trabajador_id,
            HorarioTrabajador.fecha_inicio > fecha,
        )
        .order_by(HorarioTrabajador.fecha_inicio.asc(), HorarioTrabajador.id.asc())
        .first()
    )


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
    fecha_inicio = payload["fecha_inicio"]
    same_day_schedule = (
        HorarioTrabajador.query.filter_by(
            trabajador_id=trabajador_id,
            fecha_inicio=fecha_inicio,
        )
        .order_by(HorarioTrabajador.id.desc())
        .first()
    )
    if same_day_schedule:
        # Un cambio efectivo el mismo dia reemplaza ese tramo: no crea un
        # intervalo negativo ni duplica una fila de historial.
        _apply_schedule_payload(same_day_schedule, payload)
        if (
            same_day_schedule.fecha_fin is not None
            and same_day_schedule.fecha_fin < same_day_schedule.fecha_inicio
        ):
            next_schedule = _next_schedule(trabajador_id, fecha_inicio)
            same_day_schedule.fecha_fin = (
                next_schedule.fecha_inicio - timedelta(days=1)
                if next_schedule
                else None
            )
        same_day_schedule.activo = same_day_schedule.fecha_fin is None
        return same_day_schedule, False

    previous = _schedule_covering_date(trabajador_id, fecha_inicio)
    if previous:
        previous.fecha_fin = fecha_inicio - timedelta(days=1)
        previous.activo = False

    next_schedule = _next_schedule(trabajador_id, fecha_inicio)
    fecha_fin = next_schedule.fecha_inicio - timedelta(days=1) if next_schedule else None
    schedule = HorarioTrabajador(
        trabajador_id=trabajador_id,
        fecha_fin=fecha_fin,
        activo=fecha_fin is None,
        **payload,
    )
    db.session.add(schedule)
    return schedule, True
