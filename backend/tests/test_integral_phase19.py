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
    SESSION_COOKIE_NAME = "test_session"
    PERMANENT_SESSION_LIFETIME = 3600
    FINGERPRINT_PROVIDER = "mock"
    TESTING = True


def build_integral_app():
    app = create_app(TestConfig)
    provider = MockFingerprintProvider()
    with app.app_context():
        db.create_all()
        worker_a = Trabajador(codigo="EMP-0001", nombre="Ana", apellido="Lopez", activo=True)
        worker_b = Trabajador(codigo="EMP-0002", nombre="Luis", apellido="Mendez", activo=True)
        inactive_worker = Trabajador(
            codigo="EMP-0003",
            nombre="Baja",
            apellido="Inactiva",
            activo=False,
        )
        db.session.add_all([worker_a, worker_b, inactive_worker])
        db.session.flush()

        db.session.add_all(
            [
                build_schedule(worker_a.id, time(8, 0), time(12, 45), time(13, 45)),
                build_schedule(worker_b.id, time(9, 0), time(13, 45), time(14, 45)),
                build_schedule(inactive_worker.id, time(8, 0), time(12, 45), time(13, 45)),
                Huella(
                    trabajador_id=worker_a.id,
                    template_biometrico=provider.enroll("FP-A"),
                    proveedor=provider.provider_name,
                    version=provider.version,
                    activa=True,
                ),
                Huella(
                    trabajador_id=worker_b.id,
                    template_biometrico=provider.enroll("FP-B"),
                    proveedor=provider.provider_name,
                    version=provider.version,
                    activa=True,
                ),
                Huella(
                    trabajador_id=inactive_worker.id,
                    template_biometrico=provider.enroll("FP-INACTIVE"),
                    proveedor=provider.provider_name,
                    version=provider.version,
                    activa=True,
                ),
            ]
        )
        db.session.commit()

        ids = {
            "worker_a": worker_a.id,
            "worker_b": worker_b.id,
            "inactive_worker": inactive_worker.id,
        }
    return app, ids


def build_schedule(worker_id, entrada, salida_almuerzo, regreso_almuerzo):
    return HorarioTrabajador(
        trabajador_id=worker_id,
        hora_entrada=entrada,
        hora_salida_almuerzo=salida_almuerzo,
        hora_regreso_almuerzo=regreso_almuerzo,
        hora_salida=time(18, 0),
        tolerancia_entrada=0,
        tolerancia_regreso_almuerzo=0,
        fecha_inicio=date(2026, 8, 1),
        activo=True,
    )


def test_case_1_entry_at_0800_is_valid():
    app, ids = build_integral_app()
    with app.app_context():
        result = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP-A",
            datetime(2026, 8, 20, 8, 0),
        )

    assert result["success"] is True
    assert result["data"]["marcacion"]["estado"] == ESTADO_A_TIEMPO


def test_case_2_frontend_cannot_force_exit_before_entry():
    app, ids = build_integral_app()
    with app.app_context():
        result = registrar_marcacion_biometrica(
            TIPO_SALIDA,
            "FP-A",
            datetime(2026, 8, 20, 18, 0),
        )

    assert result["success"] is True
    assert result["data"]["marcacion"]["tipo"] == TIPO_ENTRADA


def test_case_3_entry_then_forced_lunch_return_registers_lunch_exit():
    app, ids = build_integral_app()
    with app.app_context():
        entrada = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP-A",
            datetime(2026, 8, 20, 8, 0),
        )
        regreso = registrar_marcacion_biometrica(
            TIPO_REGRESO_ALMUERZO,
            "FP-A",
            datetime(2026, 8, 20, 13, 45),
        )

    assert entrada["success"] is True
    assert regreso["success"] is True
    assert regreso["data"]["marcacion"]["tipo"] == TIPO_SALIDA_ALMUERZO


def test_case_4_complete_sequence_is_valid():
    app, ids = build_integral_app()
    with app.app_context():
        entrada = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP-A",
            datetime(2026, 8, 20, 8, 0),
        )
        salida_almuerzo = registrar_marcacion_biometrica(
            TIPO_SALIDA_ALMUERZO,
            "FP-A",
            datetime(2026, 8, 20, 12, 45),
        )
        regreso = registrar_marcacion_biometrica(
            TIPO_REGRESO_ALMUERZO,
            "FP-A",
            datetime(2026, 8, 20, 13, 45),
        )
        salida = registrar_marcacion_biometrica(
            TIPO_SALIDA,
            "FP-A",
            datetime(2026, 8, 20, 18, 0),
        )
        count = Marcacion.query.filter_by(trabajador_id=ids["worker_a"]).count()

    assert entrada["success"] is True
    assert salida_almuerzo["success"] is True
    assert regreso["success"] is True
    assert salida["success"] is True
    assert count == 4


def test_case_5_second_mark_goes_to_next_pending_type():
    app, ids = build_integral_app()
    with app.app_context():
        primera = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP-A",
            datetime(2026, 8, 20, 8, 0),
        )
        duplicada = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP-A",
            datetime(2026, 8, 20, 8, 5),
        )

    assert primera["success"] is True
    assert duplicada["success"] is True
    assert duplicada["data"]["marcacion"]["tipo"] == TIPO_SALIDA_ALMUERZO


def test_case_6_inactive_worker_fingerprint_is_rejected():
    app, ids = build_integral_app()
    with app.app_context():
        result = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP-INACTIVE",
            datetime(2026, 8, 20, 8, 0),
        )

    assert result["success"] is False
    assert result["code"] == "TRABAJADOR_INACTIVO"


def test_cases_7_and_8_individual_schedules_are_respected():
    app, ids = build_integral_app()
    with app.app_context():
        worker_a = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP-A",
            datetime(2026, 8, 20, 8, 10),
        )
        worker_b = registrar_marcacion_biometrica(
            TIPO_ENTRADA,
            "FP-B",
            datetime(2026, 8, 20, 8, 10),
        )

    assert worker_a["data"]["marcacion"]["estado"] == ESTADO_TARDANZA
    assert worker_a["data"]["marcacion"]["minutos_diferencia"] == 10
    assert worker_b["data"]["marcacion"]["estado"] == ESTADO_A_TIEMPO
    assert worker_b["data"]["marcacion"]["minutos_diferencia"] == 0


def test_functional_api_does_not_accept_frontend_identity_or_time():
    app, ids = build_integral_app()
    client = app.test_client()

    response = client.post(
        "/api/marcaciones/biometrica",
        json={
            "tipo_marcacion": TIPO_ENTRADA,
            "fingerprint_id": "FP-A",
            "trabajador_id": ids["worker_b"],
            "fecha": "2026-08-20",
            "hora": "23:59",
            "estado": "A_TIEMPO",
            "minutos_diferencia": 0,
        },
    )
    data = response.get_json()["data"]["marcacion"]

    assert response.status_code == 200
    assert data["trabajador"]["codigo"] == "EMP-0001"
    assert data["hora_24"] != "23:59"
