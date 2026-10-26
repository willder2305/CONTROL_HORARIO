from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Administrador, HorarioTrabajador, Trabajador


class TestConfig:
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ["http://localhost:5173"]
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    TESTING = True


def build_client():
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
                Trabajador(codigo="EMP-0001", nombre="Ana", apellido="López"),
                Trabajador(codigo="EMP-0002", nombre="Luis", apellido="Méndez"),
            ]
        )
        db.session.commit()
    client = app.test_client()
    client.post("/api/auth/login", json={"usuario": "admin", "password": "Correcta123"})
    return app, client


def assignment_payload(fecha_inicio, entrada="08:00"):
    return {
        "fecha_inicio": fecha_inicio,
        "hora_entrada": entrada,
        "hora_salida": "17:00",
        "tolerancia_entrada": 0,
        "tolerancia_salida": 0,
        "tolerancia_regreso_almuerzo": 0,
    }


def test_login_requires_exact_username_case():
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
    assert client.post("/api/auth/login", json={"usuario": "admin", "password": "Correcta123"}).status_code == 200
    assert client.post("/api/auth/login", json={"usuario": "ADMIN", "password": "Correcta123"}).status_code == 401
    assert client.post("/api/auth/login", json={"usuario": "AdMiN", "password": "Correcta123"}).status_code == 401


def test_session_status_and_refresh_return_server_expiration():
    _, client = build_client()
    status_response = client.get("/api/auth/session")
    refresh_response = client.post("/api/auth/session/refresh")

    assert status_response.status_code == 200
    assert status_response.get_json()["data"]["seconds_remaining"] > 0
    assert refresh_response.status_code == 200
    assert refresh_response.get_json()["data"]["seconds_remaining"] > 0


def test_duplicate_worker_code_returns_only_conflict_and_preserves_worker():
    app, client = build_client()
    with app.app_context():
        first, second = Trabajador.query.order_by(Trabajador.id.asc()).all()

    response = client.put(
        f"/api/admin/trabajadores/{second.id}",
        json={"codigo": first.codigo, "nombre": "Luis", "apellido": "Méndez"},
    )

    assert response.status_code == 409
    assert response.get_json()["code"] == "CODIGO_DUPLICADO"
    with app.app_context():
        assert Trabajador.query.get(second.id).codigo == "EMP-0002"


def test_incomplete_lunch_is_rejected_with_specific_message():
    _, client = build_client()
    response = client.post(
        "/api/admin/horarios/plantillas",
        json={
            "nombre": "HORARIO INCOMPLETO",
            "hora_entrada": "08:00",
            "hora_salida_almuerzo": "12:00",
            "hora_salida": "17:00",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["code"] == "HORARIO_ALMUERZO_INCOMPLETO"
    assert response.get_json()["message"] == "Debe indicar la salida y el regreso de almuerzo."


def test_schedule_history_closes_intervals_and_replaces_same_day_assignment():
    app, client = build_client()
    with app.app_context():
        worker_id = Trabajador.query.filter_by(codigo="EMP-0001").first().id

    first = client.post(
        f"/api/admin/horarios/trabajadores/{worker_id}/asignar",
        json=assignment_payload("2026-10-01"),
    )
    second = client.post(
        f"/api/admin/horarios/trabajadores/{worker_id}/asignar",
        json=assignment_payload("2026-10-15", entrada="09:00"),
    )
    same_day = client.post(
        f"/api/admin/horarios/trabajadores/{worker_id}/asignar",
        json=assignment_payload("2026-10-15", entrada="10:00"),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert same_day.status_code == 201
    with app.app_context():
        schedules = HorarioTrabajador.query.filter_by(trabajador_id=worker_id).order_by(HorarioTrabajador.fecha_inicio.asc()).all()
        assert len(schedules) == 2
        assert schedules[0].fecha_fin == date(2026, 10, 14)
        assert schedules[0].fecha_fin >= schedules[0].fecha_inicio
        assert schedules[1].fecha_inicio == date(2026, 10, 15)
        assert schedules[1].hora_entrada.strftime("%H:%M") == "10:00"


def test_schedule_filter_rejects_invalid_value():
    _, client = build_client()
    response = client.get("/api/admin/marcaciones?horario_id=abc")

    assert response.status_code == 400
    assert response.get_json()["code"] == "FILTROS_INVALIDOS"
    assert response.get_json()["message"] == "El horario seleccionado no es válido."
