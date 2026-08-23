from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Administrador, Trabajador


class TestConfig:
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ["http://localhost:5173"]
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = 3600
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


def test_worker_crud_activate_deactivate_flow():
    app, client = build_authenticated_client()

    create_response = client.post(
        "/api/admin/trabajadores",
        json={"nombre": "Juan", "apellido": "Perez"},
    )
    worker = create_response.get_json()["data"]["trabajador"]

    list_response = client.get("/api/admin/trabajadores")
    update_response = client.put(
        f"/api/admin/trabajadores/{worker['id']}",
        json={"codigo": worker["codigo"], "nombre": "Juan Carlos", "apellido": "Perez"},
    )
    deactivate_response = client.patch(f"/api/admin/trabajadores/{worker['id']}/desactivar")
    activate_response = client.patch(f"/api/admin/trabajadores/{worker['id']}/activar")

    assert create_response.status_code == 201
    assert worker["codigo"] == "EMP-0001"
    assert list_response.status_code == 200
    assert update_response.get_json()["data"]["trabajador"]["nombre"] == "Juan Carlos"
    assert deactivate_response.get_json()["data"]["trabajador"]["activo"] is False
    assert activate_response.get_json()["data"]["trabajador"]["activo"] is True

    with app.app_context():
        assert Trabajador.query.count() == 1
        assert Trabajador.query.first().activo is True


def test_workers_api_requires_admin_session():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()

    response = app.test_client().get("/api/admin/trabajadores")

    assert response.status_code == 401
    assert response.get_json()["code"] == "NO_AUTENTICADO"
