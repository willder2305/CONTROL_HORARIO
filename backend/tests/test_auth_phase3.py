from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Administrador


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


def build_client_with_admin():
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
    return app.test_client()


def test_admin_login_success_and_me():
    client = build_client_with_admin()

    login_response = client.post(
        "/api/auth/login",
        json={"usuario": "admin", "password": "Correcta123"},
    )
    me_response = client.get("/api/auth/me")

    assert login_response.status_code == 200
    assert login_response.get_json()["success"] is True
    assert me_response.status_code == 200
    assert me_response.get_json()["data"]["admin"]["usuario"] == "admin"


def test_admin_login_rejects_bad_credentials():
    client = build_client_with_admin()

    response = client.post(
        "/api/auth/login",
        json={"usuario": "admin", "password": "incorrecta"},
    )

    assert response.status_code == 401
    assert response.get_json()["code"] == "CREDENCIALES_INVALIDAS"


def test_me_requires_session_and_logout_clears_session():
    client = build_client_with_admin()

    anonymous_response = client.get("/api/auth/me")
    client.post("/api/auth/login", json={"usuario": "admin", "password": "Correcta123"})
    logout_response = client.post("/api/auth/logout")
    after_logout_response = client.get("/api/auth/me")

    assert anonymous_response.status_code == 401
    assert logout_response.status_code == 200
    assert after_logout_response.status_code == 401
