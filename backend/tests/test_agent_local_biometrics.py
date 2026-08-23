from datetime import date, time

from app import create_app, db
from app.models import HorarioTrabajador, Huella, Marcacion, Trabajador
from app.services.attendance_service import TIPO_ENTRADA


class TestConfig:
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ["http://localhost:5173"]
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = 3600
    FINGERPRINT_PROVIDER = "local_agent"
    BIOMETRIC_AGENT_TOKEN = "agent-token"
    CSRF_PROTECT = False
    TESTING = True


def build_app_with_fingerprint():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        worker = Trabajador(codigo="EMP-0001", nombre="Juan", apellido="Perez", activo=True)
        db.session.add(worker)
        db.session.flush()
        schedule = HorarioTrabajador(
            trabajador_id=worker.id,
            hora_entrada=time(8, 0),
            hora_salida_almuerzo=time(12, 0),
            hora_regreso_almuerzo=time(13, 0),
            hora_salida=time(17, 0),
            tolerancia_entrada=0,
            tolerancia_regreso_almuerzo=0,
            fecha_inicio=date(2026, 8, 1),
            activo=True,
        )
        fingerprint = Huella(
            trabajador_id=worker.id,
            template_biometrico=b"zk-template-1",
            proveedor="local_agent",
            version="ControlHorarioBiometricAgent",
            activa=True,
        )
        inactive_worker = Trabajador(codigo="EMP-0002", nombre="Ana", apellido="Lopez", activo=False)
        db.session.add(inactive_worker)
        db.session.flush()
        inactive_fingerprint = Huella(
            trabajador_id=inactive_worker.id,
            template_biometrico=b"zk-template-2",
            proveedor="local_agent",
            version="ControlHorarioBiometricAgent",
            activa=True,
        )
        db.session.add_all([schedule, fingerprint, inactive_fingerprint])
        db.session.commit()
        fingerprint_id = fingerprint.id
    return app, fingerprint_id


def test_agent_fingerprints_requires_token():
    app, _ = build_app_with_fingerprint()
    client = app.test_client()

    response = client.get("/api/agent/fingerprints")

    assert response.status_code == 401
    assert response.get_json()["code"] == "AGENT_NO_AUTORIZADO"


def test_agent_exports_only_active_templates_without_worker_data():
    app, _ = build_app_with_fingerprint()
    client = app.test_client()

    response = client.get(
        "/api/agent/fingerprints",
        headers={"X-Agent-Token": "agent-token"},
    )

    assert response.status_code == 200
    body = response.get_json()
    fingerprints = body["data"]["fingerprints"]
    assert body["data"]["count"] == 1
    assert fingerprints[0]["template"] == "emstdGVtcGxhdGUtMQ=="
    assert "trabajador" not in fingerprints[0]
    assert "nombre" not in fingerprints[0]


def test_agent_can_register_mark_by_authorized_fingerprint_id():
    app, fingerprint_id = build_app_with_fingerprint()
    client = app.test_client()

    response = client.post(
        "/api/agent/marcaciones",
        json={"huella_id": fingerprint_id, "device_id": "ZK9500-LOCAL-01"},
        headers={"X-Agent-Token": "agent-token"},
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["marcacion"]["tipo"] == TIPO_ENTRADA
    with app.app_context():
        assert Marcacion.query.count() == 1
