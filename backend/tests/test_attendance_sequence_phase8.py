from datetime import date, datetime, time

from app import create_app, db
from app.models import HorarioTrabajador, Marcacion, Trabajador
from app.services.attendance_service import (
    TIPO_ENTRADA,
    TIPO_REGRESO_ALMUERZO,
    TIPO_SALIDA,
    TIPO_SALIDA_ALMUERZO,
    obtener_proxima_marcacion,
    validar_secuencia,
)


class TestConfig:
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ["http://localhost:5173"]
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = 3600
    FINGERPRINT_PROVIDER = "mock"
    TESTING = True


def build_worker_with_schedule():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        worker = Trabajador(codigo="EMP-0001", nombre="Juan", apellido="Perez")
        db.session.add(worker)
        db.session.flush()
        schedule = HorarioTrabajador(
            trabajador_id=worker.id,
            hora_entrada=time(8, 0),
            hora_salida_almuerzo=time(12, 45),
            hora_regreso_almuerzo=time(13, 45),
            hora_salida=time(18, 0),
            tolerancia_entrada=0,
            tolerancia_regreso_almuerzo=0,
            fecha_inicio=date(2026, 8, 1),
            activo=True,
        )
        db.session.add(schedule)
        db.session.commit()
        worker_id = worker.id
        schedule_id = schedule.id
    return app, worker_id, schedule_id


def add_mark(worker_id, schedule_id, mark_type, mark_date):
    mark_time = time(8, 0)
    if mark_type == TIPO_SALIDA_ALMUERZO:
        mark_time = time(12, 45)
    elif mark_type == TIPO_REGRESO_ALMUERZO:
        mark_time = time(13, 45)
    elif mark_type == TIPO_SALIDA:
        mark_time = time(18, 0)

    db.session.add(
        Marcacion(
            trabajador_id=worker_id,
            fecha=mark_date,
            fecha_hora=datetime.combine(mark_date, mark_time),
            tipo_marcacion=mark_type,
            hora_programada=mark_time,
            hora_real=mark_time,
            estado="A_TIEMPO",
            minutos_diferencia=0,
            horario_trabajador_id=schedule_id,
            origen="TEST",
        )
    )
    db.session.commit()


def test_salida_without_entrada_is_rejected():
    app, worker_id, schedule_id = build_worker_with_schedule()
    with app.app_context():
        result = validar_secuencia(worker_id, TIPO_SALIDA, date(2026, 8, 20))

    assert result.valido is False
    assert result.code == "SECUENCIA_INVALIDA"


def test_salida_almuerzo_without_entrada_is_rejected():
    app, worker_id, schedule_id = build_worker_with_schedule()
    with app.app_context():
        result = validar_secuencia(worker_id, TIPO_SALIDA_ALMUERZO, date(2026, 8, 20))

    assert result.valido is False
    assert result.code == "SECUENCIA_INVALIDA"


def test_regreso_almuerzo_without_salida_almuerzo_is_rejected():
    app, worker_id, schedule_id = build_worker_with_schedule()
    mark_date = date(2026, 8, 20)
    with app.app_context():
        add_mark(worker_id, schedule_id, TIPO_ENTRADA, mark_date)
        result = validar_secuencia(worker_id, TIPO_REGRESO_ALMUERZO, mark_date)

    assert result.valido is False
    assert result.code == "SECUENCIA_INVALIDA"


def test_full_sequence_is_allowed_step_by_step():
    app, worker_id, schedule_id = build_worker_with_schedule()
    mark_date = date(2026, 8, 20)
    with app.app_context():
        entrada = validar_secuencia(worker_id, TIPO_ENTRADA, mark_date)
        add_mark(worker_id, schedule_id, TIPO_ENTRADA, mark_date)

        salida_almuerzo = validar_secuencia(worker_id, TIPO_SALIDA_ALMUERZO, mark_date)
        add_mark(worker_id, schedule_id, TIPO_SALIDA_ALMUERZO, mark_date)

        regreso_almuerzo = validar_secuencia(worker_id, TIPO_REGRESO_ALMUERZO, mark_date)
        add_mark(worker_id, schedule_id, TIPO_REGRESO_ALMUERZO, mark_date)

        salida = validar_secuencia(worker_id, TIPO_SALIDA, mark_date)

    assert entrada.valido is True
    assert salida_almuerzo.valido is True
    assert regreso_almuerzo.valido is True
    assert salida.valido is True


def test_duplicate_mark_is_rejected_and_next_mark_is_calculated():
    app, worker_id, schedule_id = build_worker_with_schedule()
    mark_date = date(2026, 8, 20)
    with app.app_context():
        assert obtener_proxima_marcacion(worker_id, mark_date) == TIPO_ENTRADA
        add_mark(worker_id, schedule_id, TIPO_ENTRADA, mark_date)

        duplicate = validar_secuencia(worker_id, TIPO_ENTRADA, mark_date)
        next_mark = obtener_proxima_marcacion(worker_id, mark_date)

    assert duplicate.valido is False
    assert duplicate.code == "MARCACION_DUPLICADA"
    assert next_mark == TIPO_SALIDA_ALMUERZO
