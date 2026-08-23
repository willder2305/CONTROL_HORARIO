from datetime import date, datetime, time

from app import create_app, db
from app.models import HorarioTrabajador, Trabajador
from app.services.attendance_service import (
    ESTADO_A_TIEMPO,
    ESTADO_SALIDA_ANTICIPADA,
    ESTADO_TARDANZA,
    TIPO_ENTRADA,
    TIPO_REGRESO_ALMUERZO,
    TIPO_SALIDA,
    calcular_estado,
    preparar_datos_puntualidad,
)
from app.utils.datetime_utils import obtener_hora_actual


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
    return app, worker_id


def test_backend_time_uses_guatemala_timezone():
    now = obtener_hora_actual()

    assert now.tzinfo is not None
    assert str(now.tzinfo) == "America/Guatemala"


def test_entry_0755_for_0800_is_on_time():
    app, worker_id = build_worker_with_schedule()
    with app.app_context():
        result = preparar_datos_puntualidad(
            worker_id,
            TIPO_ENTRADA,
            datetime(2026, 8, 20, 7, 55),
        )

    assert result["estado"] == ESTADO_A_TIEMPO
    assert result["minutos_diferencia"] == 0


def test_entry_0820_for_0800_is_20_minutes_late():
    app, worker_id = build_worker_with_schedule()
    with app.app_context():
        result = preparar_datos_puntualidad(
            worker_id,
            TIPO_ENTRADA,
            datetime(2026, 8, 20, 8, 20),
        )

    assert result["estado"] == ESTADO_TARDANZA
    assert result["minutos_diferencia"] == 20


def test_lunch_return_1353_for_1345_is_8_minutes_late():
    app, worker_id = build_worker_with_schedule()
    with app.app_context():
        result = preparar_datos_puntualidad(
            worker_id,
            TIPO_REGRESO_ALMUERZO,
            datetime(2026, 8, 20, 13, 53),
        )

    assert result["estado"] == ESTADO_TARDANZA
    assert result["minutos_diferencia"] == 8


def test_exit_1735_for_1800_is_25_minutes_early():
    app, worker_id = build_worker_with_schedule()
    with app.app_context():
        result = preparar_datos_puntualidad(
            worker_id,
            TIPO_SALIDA,
            datetime(2026, 8, 20, 17, 35),
        )

    assert result["estado"] == ESTADO_SALIDA_ANTICIPADA
    assert result["minutos_diferencia"] == 25


def test_react_cannot_override_backend_time_payload_shape():
    app, worker_id = build_worker_with_schedule()
    with app.app_context():
        result = preparar_datos_puntualidad(worker_id, TIPO_ENTRADA)

    assert result["success"] is True
    assert "fecha_hora" in result
    assert "hora_real" in result
