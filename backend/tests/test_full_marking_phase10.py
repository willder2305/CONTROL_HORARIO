from datetime import date, datetime, time

from app import create_app, db
from app.models import HorarioTrabajador, Huella, Marcacion, Trabajador
from app.services.attendance_service import (
    ESTADO_A_TIEMPO,
    ESTADO_TARDANZA,
    TIPO_ENTRADA,
    TIPO_REGRESO_ALMUERZO,
    TIPO_SALIDA,
    TIPO_SALIDA_ALMUERZO,
    registrar_marcacion_biometrica,
)
from app.services.fingerprint.mock_provider import MockFingerprintProvider


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


def build_worker_with_schedule_and_fingerprint():
    app = create_app(TestConfig)
    provider = MockFingerprintProvider()
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
        fingerprint = Huella(
            trabajador_id=worker.id,
            template_biometrico=provider.enroll("FP0001"),
            proveedor=provider.provider_name,
            version=provider.version,
            activa=True,
        )
        db.session.add_all([schedule, fingerprint])
        db.session.commit()
        worker_id = worker.id
    return app, worker_id


def build_worker_without_lunch():
    app = create_app(TestConfig)
    provider = MockFingerprintProvider()
    with app.app_context():
        db.create_all()
        worker = Trabajador(codigo="EMP-0001", nombre="Juan", apellido="Perez")
        db.session.add(worker)
        db.session.flush()
        schedule = HorarioTrabajador(
            trabajador_id=worker.id,
            hora_entrada=time(8, 0),
            hora_salida_almuerzo=None,
            hora_regreso_almuerzo=None,
            hora_salida=time(16, 0),
            tolerancia_entrada=0,
            tolerancia_regreso_almuerzo=0,
            fecha_inicio=date(2026, 8, 1),
            activo=True,
        )
        fingerprint = Huella(
            trabajador_id=worker.id,
            template_biometrico=provider.enroll("FP0001"),
            proveedor=provider.provider_name,
            version=provider.version,
            activa=True,
        )
        db.session.add_all([schedule, fingerprint])
        db.session.commit()
        worker_id = worker.id
    return app, worker_id


def build_worker_without_schedule():
    app = create_app(TestConfig)
    provider = MockFingerprintProvider()
    with app.app_context():
        db.create_all()
        worker = Trabajador(codigo="EMP-0001", nombre="Juan", apellido="Perez")
        db.session.add(worker)
        db.session.flush()
        fingerprint = Huella(
            trabajador_id=worker.id,
            template_biometrico=provider.enroll("FP0001"),
            proveedor=provider.provider_name,
            version=provider.version,
            activa=True,
        )
        db.session.add(fingerprint)
        db.session.commit()
        worker_id = worker.id
    return app, worker_id


def test_complete_biometric_workday_is_registered():
    app, worker_id = build_worker_with_schedule_and_fingerprint()
    with app.app_context():
        entrada = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP0001",
            datetime(2026, 8, 20, 8, 0),
        )
        salida_almuerzo = registrar_marcacion_biometrica(
            TIPO_SALIDA_ALMUERZO,
            "FP0001",
            datetime(2026, 8, 20, 12, 45),
        )
        regreso = registrar_marcacion_biometrica(
            TIPO_REGRESO_ALMUERZO,
            "FP0001",
            datetime(2026, 8, 20, 13, 53),
        )
        salida = registrar_marcacion_biometrica(
            TIPO_SALIDA,
            "FP0001",
            datetime(2026, 8, 20, 18, 0),
        )
        count = Marcacion.query.filter_by(trabajador_id=worker_id).count()

    assert entrada["success"] is True
    assert salida_almuerzo["success"] is True
    assert regreso["data"]["marcacion"]["estado"] == ESTADO_TARDANZA
    assert regreso["data"]["marcacion"]["minutos_diferencia"] == 8
    assert salida["success"] is True
    assert count == 4


def test_frontend_type_is_ignored_and_jornada_completa_is_rejected():
    app, worker_id = build_worker_with_schedule_and_fingerprint()
    with app.app_context():
        forced_exit = registrar_marcacion_biometrica(
            TIPO_SALIDA,
            "FP0001",
            datetime(2026, 8, 20, 18, 0),
        )
        salida_almuerzo = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP0001",
            datetime(2026, 8, 20, 18, 1),
        )
        regreso = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP0001",
            datetime(2026, 8, 20, 18, 2),
        )
        salida = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP0001",
            datetime(2026, 8, 20, 18, 3),
        )
        completed = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP0001",
            datetime(2026, 8, 20, 18, 4),
        )

    assert forced_exit["success"] is True
    assert forced_exit["data"]["marcacion"]["tipo"] == TIPO_ENTRADA
    assert salida_almuerzo["data"]["marcacion"]["tipo"] == TIPO_SALIDA_ALMUERZO
    assert regreso["data"]["marcacion"]["tipo"] == TIPO_REGRESO_ALMUERZO
    assert salida["data"]["marcacion"]["tipo"] == TIPO_SALIDA
    assert completed["success"] is False
    assert completed["code"] == "JORNADA_COMPLETADA"


def test_unknown_fingerprint_is_rejected_for_marking():
    app, worker_id = build_worker_with_schedule_and_fingerprint()
    with app.app_context():
        result = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP9999",
            datetime(2026, 8, 20, 8, 0),
        )

    assert result["success"] is False
    assert result["code"] == "HUELLA_NO_RECONOCIDA"


def test_schedule_without_lunch_uses_entry_exit_sequence():
    app, worker_id = build_worker_without_lunch()
    with app.app_context():
        entrada = registrar_marcacion_biometrica(
            TIPO_SALIDA_ALMUERZO,
            "FP0001",
            datetime(2026, 8, 20, 8, 0),
        )
        salida = registrar_marcacion_biometrica(
            TIPO_REGRESO_ALMUERZO,
            "FP0001",
            datetime(2026, 8, 20, 16, 0),
        )
        completed = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP0001",
            datetime(2026, 8, 20, 16, 2),
        )
        marks = Marcacion.query.filter_by(trabajador_id=worker_id).order_by(Marcacion.id).all()

    assert entrada["data"]["marcacion"]["tipo"] == TIPO_ENTRADA
    assert salida["data"]["marcacion"]["tipo"] == TIPO_SALIDA
    assert completed["code"] == "JORNADA_COMPLETADA"
    assert [mark.tipo_marcacion for mark in marks] == [TIPO_ENTRADA, TIPO_SALIDA]


def test_worker_without_schedule_does_not_register_mark():
    app, worker_id = build_worker_without_schedule()
    with app.app_context():
        result = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP0001",
            datetime(2026, 8, 20, 8, 0),
        )
        count = Marcacion.query.filter_by(trabajador_id=worker_id).count()

    assert result["success"] is False
    assert result["code"] == "HORARIO_NO_ASIGNADO"
    assert count == 0


def test_immediate_double_request_is_rejected():
    app, worker_id = build_worker_with_schedule_and_fingerprint()
    with app.app_context():
        first = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP0001",
            datetime(2026, 8, 20, 8, 0),
        )
        second = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP0001",
            datetime(2026, 8, 20, 8, 0, 5),
        )
        count = Marcacion.query.filter_by(trabajador_id=worker_id).count()

    assert first["success"] is True
    assert second["success"] is False
    assert second["code"] == "MARCACION_RECIENTE"
    assert count == 1


def test_endpoint_ignores_frontend_sent_time():
    app, worker_id = build_worker_with_schedule_and_fingerprint()
    client = app.test_client()

    response = client.post(
        "/api/marcaciones/biometrica",
        json={
            "tipo_marcacion": TIPO_ENTRADA,
            "fingerprint_id": "FP0001",
            "hora": "23:59",
            "trabajador_id": 999,
        },
    )

    assert response.status_code == 200
    data = response.get_json()["data"]["marcacion"]
    assert data["hora_24"] != "23:59"
    assert data["trabajador"]["codigo"] == "EMP-0001"
