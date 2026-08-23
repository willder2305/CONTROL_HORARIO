from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Administrador, Auditoria, Trabajador


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


def build_authenticated_client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        db.session.add(
            Administrador(
                usuario="admin",
                password_hash=generate_password_hash("Correcta123"),
                nombre="Admin",
                apellido="Principal",
                activo=True,
            )
        )
        db.session.commit()

    client = app.test_client()
    client.post("/api/auth/login", json={"usuario": "admin", "password": "Correcta123"})
    return app, client


def audit_actions():
    return [audit.accion for audit in Auditoria.query.order_by(Auditoria.id.asc()).all()]


def test_worker_changes_are_audited():
    app, client = build_authenticated_client()

    create_response = client.post(
        "/api/admin/trabajadores",
        json={"nombre": "Juan", "apellido": "Perez"},
    )
    worker = create_response.get_json()["data"]["trabajador"]
    client.put(
        f"/api/admin/trabajadores/{worker['id']}",
        json={"codigo": worker["codigo"], "nombre": "Juan Carlos", "apellido": "Perez"},
    )
    client.patch(f"/api/admin/trabajadores/{worker['id']}/desactivar")
    client.patch(f"/api/admin/trabajadores/{worker['id']}/activar")

    with app.app_context():
        actions = audit_actions()
        first_audit = Auditoria.query.order_by(Auditoria.id.asc()).first()

    assert actions == [
        "CREAR_TRABAJADOR",
        "EDITAR_TRABAJADOR",
        "DESACTIVAR_TRABAJADOR",
        "ACTIVAR_TRABAJADOR",
    ]
    assert first_audit.administrador_id is not None
    assert first_audit.entidad == "trabajadores"
    assert first_audit.ip is not None


def test_schedule_assignment_and_modification_are_audited_separately():
    app, client = build_authenticated_client()
    worker_response = client.post(
        "/api/admin/trabajadores",
        json={"nombre": "Ana", "apellido": "Lopez"},
    )
    worker_id = worker_response.get_json()["data"]["trabajador"]["id"]

    client.post(
        f"/api/admin/horarios/trabajadores/{worker_id}/asignar",
        json={
            "fecha_inicio": "2026-08-01",
            "hora_entrada": "08:00",
            "hora_salida_almuerzo": "12:45",
            "hora_regreso_almuerzo": "13:45",
            "hora_salida": "18:00",
            "tolerancia_entrada": 0,
            "tolerancia_regreso_almuerzo": 0,
        },
    )
    client.post(
        f"/api/admin/horarios/trabajadores/{worker_id}/asignar",
        json={
            "fecha_inicio": "2026-09-01",
            "hora_entrada": "09:00",
            "hora_salida_almuerzo": "13:45",
            "hora_regreso_almuerzo": "14:45",
            "hora_salida": "18:00",
            "tolerancia_entrada": 5,
            "tolerancia_regreso_almuerzo": 0,
        },
    )

    with app.app_context():
        actions = audit_actions()

    assert "ASIGNAR_HORARIO" in actions
    assert "MODIFICAR_HORARIO" in actions


def test_fingerprint_registration_and_replacement_are_audited():
    app, client = build_authenticated_client()
    worker_response = client.post(
        "/api/admin/trabajadores",
        json={"nombre": "Luis", "apellido": "Mendez"},
    )
    worker_id = worker_response.get_json()["data"]["trabajador"]["id"]

    client.post(
        f"/api/biometria/trabajadores/{worker_id}/registrar",
        json={"fingerprint_id": "FP0001"},
    )
    client.post(
        f"/api/biometria/trabajadores/{worker_id}/registrar",
        json={"fingerprint_id": "FP0002"},
    )

    with app.app_context():
        actions = audit_actions()

    assert "REGISTRAR_HUELLA" in actions
    assert "REEMPLAZAR_HUELLA" in actions
