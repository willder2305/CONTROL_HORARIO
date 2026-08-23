from datetime import datetime

from flask import Blueprint, jsonify, request

from app.models import Marcacion, Trabajador
from app.routes.auth import require_admin

from app.services.attendance_service import registrar_marcacion_biometrica
from app.utils.datetime_utils import obtener_hora_actual

marcaciones_bp = Blueprint("marcaciones", __name__)
admin_marcaciones_bp = Blueprint("admin_marcaciones", __name__)


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def serialize_time(value):
    return value.strftime("%H:%M") if value else None


def serialize_mark(mark):
    worker = mark.trabajador
    return {
        "id": mark.id,
        "fecha": mark.fecha.isoformat(),
        "trabajador_id": mark.trabajador_id,
        "codigo": worker.codigo if worker else None,
        "nombre": worker.nombre if worker else None,
        "apellido": worker.apellido if worker else None,
        "tipo_marcacion": mark.tipo_marcacion,
        "hora_programada": serialize_time(mark.hora_programada),
        "hora_real": serialize_time(mark.hora_real),
        "estado": mark.estado,
        "minutos_diferencia": mark.minutos_diferencia,
        "horario_trabajador_id": mark.horario_trabajador_id,
        "origen": mark.origen,
        "observacion": mark.observacion,
        "created_at": mark.created_at.isoformat() if mark.created_at else None,
    }


def build_mark_query(args):
    query = Marcacion.query.join(Trabajador)

    trabajador_id = args.get("trabajador_id")
    tipo_marcacion = (args.get("tipo_marcacion") or "").strip().upper()
    estado = (args.get("estado") or "").strip().upper()
    horario_id = args.get("horario_id")
    fecha = parse_date(args.get("fecha"))
    desde = parse_date(args.get("desde"))
    hasta = parse_date(args.get("hasta"))

    if trabajador_id:
        query = query.filter(Marcacion.trabajador_id == int(trabajador_id))
    if tipo_marcacion:
        query = query.filter(Marcacion.tipo_marcacion == tipo_marcacion)
    if estado:
        query = query.filter(Marcacion.estado == estado)
    if horario_id:
        query = query.filter(Marcacion.horario_trabajador_id == int(horario_id))
    if fecha:
        query = query.filter(Marcacion.fecha == fecha)
    if desde:
        query = query.filter(Marcacion.fecha >= desde)
    if hasta:
        query = query.filter(Marcacion.fecha <= hasta)

    return query


def empty_day_row(mark):
    worker = mark.trabajador
    return {
        "fecha": mark.fecha.isoformat(),
        "trabajador_id": mark.trabajador_id,
        "codigo": worker.codigo if worker else None,
        "trabajador": f"{worker.nombre} {worker.apellido}" if worker else "",
        "entrada": None,
        "salida_almuerzo": None,
        "regreso_almuerzo": None,
        "salida": None,
        "estado": "SIN_MARCACIONES",
    }


def set_day_mark(row, mark):
    value = {
        "hora": serialize_time(mark.hora_real),
        "estado": mark.estado,
        "minutos_diferencia": mark.minutos_diferencia,
    }
    mapping = {
        "ENTRADA": "entrada",
        "SALIDA_ALMUERZO": "salida_almuerzo",
        "REGRESO_ALMUERZO": "regreso_almuerzo",
        "SALIDA": "salida",
    }
    key = mapping.get(mark.tipo_marcacion)
    if key:
        row[key] = value


def calculate_day_status(row):
    states = [
        row[key]["estado"]
        for key in ("entrada", "salida_almuerzo", "regreso_almuerzo", "salida")
        if row[key]
    ]
    if "TARDANZA" in states:
        return "TARDANZA"
    if "SALIDA_ANTICIPADA" in states:
        return "SALIDA_ANTICIPADA"
    if "ANTICIPADO" in states:
        return "ANTICIPADO"
    if states and all(state == "A_TIEMPO" for state in states):
        return "A_TIEMPO"
    return "INCOMPLETO"


def build_day_rows(marks):
    rows = {}
    for mark in marks:
        key = (mark.fecha, mark.trabajador_id)
        if key not in rows:
            rows[key] = empty_day_row(mark)
        set_day_mark(rows[key], mark)
    for row in rows.values():
        row["estado"] = calculate_day_status(row)
    return list(rows.values())


def build_dashboard_stats(fecha):
    active_workers = Trabajador.query.filter_by(activo=True).all()
    active_worker_ids = {worker.id for worker in active_workers}
    marks = (
        Marcacion.query.filter(Marcacion.fecha == fecha)
        .filter(Marcacion.trabajador_id.in_(active_worker_ids) if active_worker_ids else False)
        .all()
    )
    marks_by_worker = {}
    for mark in marks:
        marks_by_worker.setdefault(mark.trabajador_id, {})[mark.tipo_marcacion] = mark

    presentes_hoy = sum(1 for values in marks_by_worker.values() if "ENTRADA" in values)
    entradas_registradas = sum(1 for mark in marks if mark.tipo_marcacion == "ENTRADA")
    tardanzas = sum(1 for mark in marks if mark.estado == "TARDANZA")
    regresos_tardios = sum(
        1
        for mark in marks
        if mark.tipo_marcacion == "REGRESO_ALMUERZO" and mark.estado == "TARDANZA"
    )
    salidas = sum(1 for mark in marks if mark.tipo_marcacion == "SALIDA")
    en_almuerzo = sum(
        1
        for values in marks_by_worker.values()
        if "SALIDA_ALMUERZO" in values and "REGRESO_ALMUERZO" not in values
    )
    pendientes_salida = sum(
        1
        for values in marks_by_worker.values()
        if "ENTRADA" in values and "SALIDA" not in values
    )

    return {
        "fecha": fecha.isoformat(),
        "trabajadores_activos": len(active_workers),
        "presentes_hoy": presentes_hoy,
        "entradas_registradas": entradas_registradas,
        "tardanzas": tardanzas,
        "en_almuerzo": en_almuerzo,
        "regresos_tardios": regresos_tardios,
        "salidas": salidas,
        "pendientes_salida": pendientes_salida,
    }


@marcaciones_bp.post("/biometrica")
def create_biometric_mark():
    data = request.get_json(silent=True) or {}
    fingerprint_id = (data.get("fingerprint_id") or "").strip().upper()

    result = registrar_marcacion_biometrica(fingerprint_id=fingerprint_id)
    status_code = 200 if result["success"] else 400
    if result.get("code") == "HUELLA_NO_RECONOCIDA":
        status_code = 404
    elif result.get("code") == "LECTOR_NO_DISPONIBLE":
        status_code = 503
    elif result.get("code") in {
        "TRABAJADOR_INACTIVO",
        "SECUENCIA_INVALIDA",
        "JORNADA_COMPLETADA",
        "MARCACION_RECIENTE",
    }:
        status_code = 409
    elif result.get("code") == "MARCACION_DUPLICADA":
        status_code = 409

    return jsonify(result), status_code


@admin_marcaciones_bp.get("")
@require_admin
def list_admin_marks():
    try:
        query = build_mark_query(request.args)
    except ValueError:
        return (
            jsonify(
                {
                    "success": False,
                    "code": "FILTROS_INVALIDOS",
                    "message": "Revise el formato de fechas y filtros numericos.",
                }
            ),
            400,
        )

    marks = query.order_by(
        Marcacion.fecha.desc(),
        Trabajador.codigo.asc(),
        Marcacion.fecha_hora.asc(),
    ).all()
    return jsonify(
        {
            "success": True,
            "data": {
                "jornada": build_day_rows(marks),
                "marcaciones": [serialize_mark(mark) for mark in marks],
            },
        }
    )


@admin_marcaciones_bp.get("/dashboard")
@require_admin
def dashboard_stats():
    fecha = parse_date(request.args.get("fecha")) or obtener_hora_actual().date()
    return jsonify({"success": True, "data": build_dashboard_stats(fecha)})
