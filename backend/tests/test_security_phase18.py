from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Administrador


class SecurityConfig:
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
    CSRF_PROTECT = True
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024


def build_security_client():
    app = create_app(SecurityConfig)
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
    login_response = client.post(
        "/api/auth/login",
        json={"usuario": "admin", "password": "Correcta123"},
    )
    csrf_token = login_response.get_json()["data"]["csrf_token"]
    return app, client, csrf_token


def test_security_headers_are_added_to_api_responses():
    app = create_app(SecurityConfig)
    with app.app_context():
        db.create_all()

    response = app.test_client().get("/api/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"


def test_admin_mutation_requires_csrf_token_when_enabled():
    app, client, csrf_token = build_security_client()

    response = client.post(
        "/api/admin/trabajadores",
        json={"nombre": "Juan", "apellido": "Perez"},
    )

    assert response.status_code == 403
    assert response.get_json()["code"] == "CSRF_INVALIDO"


def test_admin_mutation_accepts_valid_csrf_token():
    app, client, csrf_token = build_security_client()

    response = client.post(
        "/api/admin/trabajadores",
        headers={"X-CSRF-Token": csrf_token},
        json={"nombre": "Juan", "apellido": "Perez"},
    )

    assert response.status_code == 201


def test_logout_requires_csrf_token_when_enabled():
    app, client, csrf_token = build_security_client()

    rejected = client.post("/api/auth/logout")
    accepted = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_token})

    assert rejected.status_code == 403
    assert accepted.status_code == 200
