"""Modulo commands del sistema de control de horarios.

Agrupa la logica propia necesaria para esta responsabilidad sin exponer detalles de infraestructura.
"""

import getpass
from collections import defaultdict
from datetime import time

import click
from werkzeug.security import generate_password_hash

from app import db
from app.models import Administrador, HorarioTrabajador, PlantillaHorario


def register_commands(app):
    """
    Implementa la responsabilidad de register commands dentro de este modulo.

    Args:
        app: Dato utilizado por la operacion.

    Returns:
        Resultado de la operacion o respuesta HTTP correspondiente.
    """
    app.cli.add_command(create_admin_command)
    app.cli.add_command(seed_schedules_command)
    app.cli.add_command(audit_schedule_history_command)


@click.command("crear-admin")
@click.option("--usuario", prompt=True, help="Usuario administrador.")
@click.option("--nombre", prompt=True, help="Nombre del administrador.")
@click.option("--apellido", prompt=True, help="Apellido del administrador.")
def create_admin_command(usuario, nombre, apellido):
    """
    Crea un administrador inicial con contrasena solicitada de forma segura.

    Recibe:
        usuario, nombre y apellido por opciones CLI.

    Utilizado desde:
        flask crear-admin

    Retorna:
        Mensaje en consola con el resultado.
    """
    if Administrador.query.filter_by(usuario=usuario).first():
        raise click.ClickException("Ya existe un administrador con ese usuario.")

    password = getpass.getpass("Contrasena: ")
    password_confirm = getpass.getpass("Confirmar contrasena: ")

    if not password:
        raise click.ClickException("La contrasena no puede estar vacia.")
    if password != password_confirm:
        raise click.ClickException("Las contrasenas no coinciden.")

    admin = Administrador(
        usuario=usuario,
        password_hash=generate_password_hash(password),
        nombre=nombre,
        apellido=apellido,
        activo=True,
    )
    db.session.add(admin)
    db.session.commit()
    click.echo("Administrador creado correctamente.")


@click.command("seed-horarios")
def seed_schedules_command():
    """
    Crea las plantillas iniciales de horario de la farmacia.

    Recibe:
        No recibe parametros.

    Utilizado desde:
        flask seed-horarios

    Retorna:
        Mensaje en consola con el resultado.
    """
    templates = [
        {
            "nombre": "HORARIO A",
            "hora_entrada": time(8, 0),
            "hora_salida_almuerzo": time(12, 45),
            "hora_regreso_almuerzo": time(13, 45),
            "hora_salida": time(18, 0),
            "tolerancia_entrada": 0,
            "tolerancia_salida": 0,
            "tolerancia_regreso_almuerzo": 0,
        },
        {
            "nombre": "HORARIO B",
            "hora_entrada": time(8, 0),
            "hora_salida_almuerzo": time(13, 45),
            "hora_regreso_almuerzo": time(14, 45),
            "hora_salida": time(18, 0),
            "tolerancia_entrada": 0,
            "tolerancia_salida": 0,
            "tolerancia_regreso_almuerzo": 0,
        },
    ]

    created = 0
    for data in templates:
        if PlantillaHorario.query.filter_by(nombre=data["nombre"]).first():
            continue
        db.session.add(PlantillaHorario(**data))
        created += 1

    db.session.commit()
    click.echo(f"Plantillas iniciales creadas: {created}.")


def schedule_identity(schedule):
    """Construye una clave de igualdad exacta sin incluir datos biométricos."""
    return (
        schedule.trabajador_id,
        schedule.plantilla_id,
        schedule.hora_entrada,
        schedule.hora_salida_almuerzo,
        schedule.hora_regreso_almuerzo,
        schedule.hora_salida,
        schedule.tolerancia_entrada,
        schedule.tolerancia_salida,
        schedule.tolerancia_regreso_almuerzo,
        schedule.fecha_inicio,
        schedule.fecha_fin,
    )


@click.command("auditar-historial-horarios")
def audit_schedule_history_command():
    """Lista anomalías del historial sin modificar ningún registro."""
    schedules = HorarioTrabajador.query.order_by(
        HorarioTrabajador.trabajador_id.asc(),
        HorarioTrabajador.fecha_inicio.asc(),
        HorarioTrabajador.id.asc(),
    ).all()

    invalid_dates = [
        schedule
        for schedule in schedules
        if schedule.fecha_fin is not None and schedule.fecha_fin < schedule.fecha_inicio
    ]
    by_identity = defaultdict(list)
    by_worker = defaultdict(list)
    for schedule in schedules:
        by_identity[schedule_identity(schedule)].append(schedule)
        by_worker[schedule.trabajador_id].append(schedule)

    duplicates = [group for group in by_identity.values() if len(group) > 1]
    overlaps = []
    for worker_id, worker_schedules in by_worker.items():
        previous = None
        for schedule in worker_schedules:
            if previous is not None and (
                previous.fecha_fin is None or schedule.fecha_inicio <= previous.fecha_fin
            ):
                overlaps.append((worker_id, previous.id, schedule.id))
            if previous is None or previous.fecha_fin is None or (
                schedule.fecha_fin is not None and schedule.fecha_fin > previous.fecha_fin
            ):
                previous = schedule

    click.echo(f"Registros analizados: {len(schedules)}")
    click.echo(f"Fechas invertidas: {len(invalid_dates)}")
    for schedule in invalid_dates:
        click.echo(
            f"  horario_id={schedule.id} trabajador_id={schedule.trabajador_id} "
            f"inicio={schedule.fecha_inicio.isoformat()} fin={schedule.fecha_fin.isoformat()}"
        )
    click.echo(f"Grupos duplicados exactos: {len(duplicates)}")
    for group in duplicates:
        click.echo(
            f"  trabajador_id={group[0].trabajador_id} horarios={','.join(str(item.id) for item in group)}"
        )
    click.echo(f"Solapamientos: {len(overlaps)}")
    for worker_id, first_id, second_id in overlaps:
        click.echo(
            f"  trabajador_id={worker_id} horarios={first_id},{second_id}"
        )

    if invalid_dates or duplicates or overlaps:
        raise click.ClickException(
            "Auditoría con hallazgos. Revise el backup y corrija cada caso de forma controlada."
        )
