from flask import Blueprint, jsonify, request, send_file

from app.models import Marcacion, Trabajador
from app.routes.auth import require_admin
from app.routes.marcaciones import build_mark_query, serialize_mark
from app.services.report_service import build_excel_report, build_pdf_report

reportes_bp = Blueprint("reportes", __name__)


def build_summary(marks):
    total = len(marks)
    tardanzas = sum(1 for mark in marks if mark.estado == "TARDANZA")
    a_tiempo = sum(1 for mark in marks if mark.estado == "A_TIEMPO")
    salidas_anticipadas = sum(
        1 for mark in marks if mark.estado == "SALIDA_ANTICIPADA"
    )
    anticipados = sum(1 for mark in marks if mark.estado == "ANTICIPADO")
    trabajadores = len({mark.trabajador_id for mark in marks})

    return {
        "total_marcaciones": total,
        "total_tardanzas": tardanzas,
        "total_a_tiempo": a_tiempo,
        "total_salidas_anticipadas": salidas_anticipadas,
        "total_anticipados": anticipados,
        "trabajadores_incluidos": trabajadores,
    }


def describe_filters(args):
    return {
        "trabajador_id": args.get("trabajador_id") or None,
        "tipo_marcacion": args.get("tipo_marcacion") or None,
        "estado": args.get("estado") or None,
        "fecha": args.get("fecha") or None,
        "desde": args.get("desde") or None,
        "hasta": args.get("hasta") or None,
    }


def describe_pdf_filters(args):
    fecha = args.get("fecha")
    desde = args.get("desde")
    hasta = args.get("hasta")
    worker_label = "Todos"
    worker_id = args.get("trabajador_id")

    if worker_id:
        worker = Trabajador.query.get(int(worker_id))
        if worker:
            worker_label = f"{worker.codigo} - {worker.nombre} {worker.apellido}"
        else:
            worker_label = f"ID {worker_id}"

    if fecha:
        range_label = f"{fecha} a {fecha}"
    elif desde or hasta:
        range_label = f"{desde or 'inicio'} a {hasta or 'fin'}"
    else:
        range_label = "Todos"

    return {
        "rango": range_label,
        "trabajador": worker_label,
        "tipo": args.get("tipo_marcacion") or "Todos",
        "estado": args.get("estado") or "Todos",
    }


def get_ordered_report_marks(args):
    query = build_mark_query(args)
    return query.order_by(
        Marcacion.fecha.asc(),
        Trabajador.codigo.asc(),
        Marcacion.fecha_hora.asc(),
    ).all()


@reportes_bp.get("")
@require_admin
def screen_report():
    try:
        marks = get_ordered_report_marks(request.args)
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

    return jsonify(
        {
            "success": True,
            "data": {
                "filtros": describe_filters(request.args),
                "resumen": build_summary(marks),
                "resultados": [serialize_mark(mark) for mark in marks],
            },
        }
    )


@reportes_bp.get("/excel")
@require_admin
def excel_report():
    try:
        marks = get_ordered_report_marks(request.args)
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

    report_file = build_excel_report(marks)

    return send_file(
        report_file,
        as_attachment=True,
        download_name="reporte_control_horarios.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@reportes_bp.get("/pdf")
@require_admin
def pdf_report():
    try:
        marks = get_ordered_report_marks(request.args)
        filters = describe_pdf_filters(request.args)
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

    report_file = build_pdf_report(marks, filters, build_summary(marks))

    return send_file(
        report_file,
        as_attachment=True,
        download_name="reporte_control_horarios.pdf",
        mimetype="application/pdf",
    )
