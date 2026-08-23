import getpass
from datetime import time

import click
from werkzeug.security import generate_password_hash

from app import db
from app.models import Administrador, PlantillaHorario


def register_commands(app):
    app.cli.add_command(create_admin_command)
    app.cli.add_command(seed_schedules_command)


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
            "tolerancia_regreso_almuerzo": 0,
        },
        {
            "nombre": "HORARIO B",
            "hora_entrada": time(8, 0),
            "hora_salida_almuerzo": time(13, 45),
            "hora_regreso_almuerzo": time(14, 45),
            "hora_salida": time(18, 0),
            "tolerancia_entrada": 0,
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
