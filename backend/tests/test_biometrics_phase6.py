from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Administrador, Huella, Trabajador


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
        db.session.add_all(
            [
                Trabajador(codigo="EMP-0001", nombre="Juan", apellido="Perez"),
                Trabajador(codigo="EMP-0002", nombre="Maria", apellido="Lopez"),
            ]
        )
        db.session.commit()

    client = app.test_client()
    client.post("/api/auth/login", json={"usuario": "admin", "password": "Correcta123"})
    return app, client


def test_register_and_identify_mock_fingerprint():
    app, client = build_authenticated_client()
    with app.app_context():
        worker_id = Trabajador.query.filter_by(codigo="EMP-0001").first().id

    register_response = client.post(
        f"/api/biometria/trabajadores/{worker_id}/registrar",
        json={"fingerprint_id": "FP0001"},
    )
    identify_response = client.post(
        "/api/biometria/identificar",
        json={"fingerprint_id": "FP0001"},
    )

    assert register_response.status_code == 201
    assert "template_biometrico" not in register_response.get_data(as_text=True)
    assert identify_response.status_code == 200
    assert identify_response.get_json()["data"]["trabajador"]["codigo"] == "EMP-0001"


def test_unknown_mock_fingerprint_is_rejected():
    app, client = build_authenticated_client()

    response = client.post("/api/biometria/identificar", json={"fingerprint_id": "FP9999"})

    assert response.status_code == 404
    assert response.get_json()["code"] == "HUELLA_NO_RECONOCIDA"


def test_duplicate_fingerprint_for_another_worker_is_rejected():
    app, client = build_authenticated_client()
    with app.app_context():
        worker_a = Trabajador.query.filter_by(codigo="EMP-0001").first().id
        worker_b = Trabajador.query.filter_by(codigo="EMP-0002").first().id

    client.post(
        f"/api/biometria/trabajadores/{worker_a}/registrar",
        json={"fingerprint_id": "FP0001"},
    )
    duplicate_response = client.post(
        f"/api/biometria/trabajadores/{worker_b}/registrar",
        json={"fingerprint_id": "FP0001"},
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.get_json()["code"] == "HUELLA_DUPLICADA"


def test_replacing_worker_fingerprint_deactivates_previous_one():
    app, client = build_authenticated_client()
    with app.app_context():
        worker_id = Trabajador.query.filter_by(codigo="EMP-0001").first().id

    client.post(
        f"/api/biometria/trabajadores/{worker_id}/registrar",
        json={"fingerprint_id": "FP0001"},
    )
    replace_response = client.post(
        f"/api/biometria/trabajadores/{worker_id}/registrar",
        json={"fingerprint_id": "FP0003"},
    )

    with app.app_context():
        active_count = Huella.query.filter_by(trabajador_id=worker_id, activa=True).count()
        total_count = Huella.query.filter_by(trabajador_id=worker_id).count()

    assert replace_response.status_code == 201
    assert active_count == 1
    assert total_count == 2
