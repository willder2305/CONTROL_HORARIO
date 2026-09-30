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


def build_worker_with_schedule(
    hora_salida=time(18, 0),
    tolerancia_entrada=0,
    tolerancia_salida=0,
    con_almuerzo=True,
):
    """Crea un horario de prueba configurable para verificar puntualidad sin depender de MySQL."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        worker = Trabajador(codigo="EMP-0001", nombre="Juan", apellido="Perez")
        db.session.add(worker)
        db.session.flush()
        schedule = HorarioTrabajador(
            trabajador_id=worker.id,
            hora_entrada=time(8, 0),
            hora_salida_almuerzo=time(12, 45) if con_almuerzo else None,
            hora_regreso_almuerzo=time(13, 45) if con_almuerzo else None,
            hora_salida=hora_salida,
            tolerancia_entrada=tolerancia_entrada,
            tolerancia_salida=tolerancia_salida,
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


def test_exit_before_tolerance_is_early_with_the_real_advance_minutes():
    app, worker_id = build_worker_with_schedule(
        hora_salida=time(17, 0),
        tolerancia_salida=10,
    )
    with app.app_context():
        result = preparar_datos_puntualidad(
            worker_id,
            TIPO_SALIDA,
            datetime(2026, 8, 20, 16, 49),
        )

    assert result["estado"] == ESTADO_SALIDA_ANTICIPADA
    assert result["minutos_diferencia"] == 11


def test_exit_at_tolerance_limit_is_on_time():
    app, worker_id = build_worker_with_schedule(
        hora_salida=time(17, 0),
        tolerancia_salida=10,
    )
    with app.app_context():
        result = preparar_datos_puntualidad(
            worker_id,
            TIPO_SALIDA,
            datetime(2026, 8, 20, 16, 50),
        )

    assert result["estado"] == ESTADO_A_TIEMPO
    assert result["minutos_diferencia"] == 0


def test_exit_within_tolerance_at_schedule_and_after_schedule_are_on_time():
    app, worker_id = build_worker_with_schedule(
        hora_salida=time(17, 0),
        tolerancia_salida=10,
    )
    with app.app_context():
        for actual_time in (time(16, 55), time(17, 0), time(17, 30)):
            estado, minutos_diferencia = calcular_estado(
                TIPO_SALIDA,
                actual_time,
                time(17, 0),
                db.session.get(HorarioTrabajador, 1),
            )
            assert estado == ESTADO_A_TIEMPO
            assert minutos_diferencia == 0


def test_exit_with_zero_tolerance_is_early_only_before_the_scheduled_time():
    app, worker_id = build_worker_with_schedule(hora_salida=time(17, 0))
    with app.app_context():
        early_result = preparar_datos_puntualidad(
            worker_id,
            TIPO_SALIDA,
            datetime(2026, 8, 20, 16, 59),
        )
        on_time_result = preparar_datos_puntualidad(
            worker_id,
            TIPO_SALIDA,
            datetime(2026, 8, 20, 17, 0),
        )

    assert early_result["estado"] == ESTADO_SALIDA_ANTICIPADA
    assert early_result["minutos_diferencia"] == 1
    assert on_time_result["estado"] == ESTADO_A_TIEMPO
    assert on_time_result["minutos_diferencia"] == 0


def test_exit_tolerance_applies_to_a_schedule_without_lunch():
    app, worker_id = build_worker_with_schedule(
        hora_salida=time(17, 0),
        tolerancia_salida=10,
        con_almuerzo=False,
    )
    with app.app_context():
        result = preparar_datos_puntualidad(
            worker_id,
            TIPO_SALIDA,
            datetime(2026, 8, 20, 16, 49),
        )

    assert result["estado"] == ESTADO_SALIDA_ANTICIPADA


def test_entry_tolerance_regression_keeps_0810_on_time_and_0811_late():
    app, worker_id = build_worker_with_schedule(tolerancia_entrada=10)
    with app.app_context():
        on_time_result = preparar_datos_puntualidad(
            worker_id,
            TIPO_ENTRADA,
            datetime(2026, 8, 20, 8, 10),
        )
        late_result = preparar_datos_puntualidad(
            worker_id,
            TIPO_ENTRADA,
            datetime(2026, 8, 20, 8, 11),
        )

    assert on_time_result["estado"] == ESTADO_A_TIEMPO
    assert on_time_result["minutos_diferencia"] == 0
    assert late_result["estado"] == ESTADO_TARDANZA
    assert late_result["minutos_diferencia"] == 1


def test_react_cannot_override_backend_time_payload_shape():
    app, worker_id = build_worker_with_schedule()
    with app.app_context():
        result = preparar_datos_puntualidad(worker_id, TIPO_ENTRADA)

    assert result["success"] is True
    assert "fecha_hora" in result
    assert "hora_real" in result
