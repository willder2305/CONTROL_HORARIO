from datetime import date

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
        db.session.add_all(
            [
                Trabajador(codigo="EMP-0001", nombre="Ana", apellido="Lopez"),
                Trabajador(codigo="EMP-0002", nombre="Luis", apellido="Mendez"),
            ]
        )
        db.session.commit()

    client = app.test_client()
    client.post("/api/auth/login", json={"usuario": "admin", "password": "Correcta123"})
    return app, client


def test_template_crud_and_deactivate():
    app, client = build_authenticated_client()

    create_response = client.post(
        "/api/admin/horarios/plantillas",
        json={
            "nombre": "Horario C",
            "hora_entrada": "09:00",
            "hora_salida_almuerzo": "13:45",
            "hora_regreso_almuerzo": "14:45",
            "hora_salida": "18:00",
            "tolerancia_entrada": 5,
            "tolerancia_regreso_almuerzo": 3,
        },
    )
    template = create_response.get_json()["data"]["plantilla"]

    update_response = client.put(
        f"/api/admin/horarios/plantillas/{template['id']}",
        json={**template, "nombre": "Horario C Editado", "hora_entrada": "09:15"},
    )
    deactivate_response = client.patch(
        f"/api/admin/horarios/plantillas/{template['id']}/desactivar"
    )

    assert create_response.status_code == 201
    assert update_response.get_json()["data"]["plantilla"]["hora_entrada"] == "09:15"
    assert deactivate_response.get_json()["data"]["plantilla"]["activo"] is False


def test_assign_independent_worker_schedules_and_history():
    app, client = build_authenticated_client()

    template_response = client.post(
        "/api/admin/horarios/plantillas",
        json={
            "nombre": "Horario A",
            "hora_entrada": "08:00",
            "hora_salida_almuerzo": "12:45",
            "hora_regreso_almuerzo": "13:45",
            "hora_salida": "18:00",
            "tolerancia_entrada": 0,
            "tolerancia_regreso_almuerzo": 0,
        },
    )
    template_id = template_response.get_json()["data"]["plantilla"]["id"]

    with app.app_context():
        worker_a_id = Trabajador.query.filter_by(codigo="EMP-0001").first().id
        worker_b_id = Trabajador.query.filter_by(codigo="EMP-0002").first().id

    assign_a = client.post(
        f"/api/admin/horarios/trabajadores/{worker_a_id}/asignar",
        json={"plantilla_id": template_id, "fecha_inicio": "2026-08-01"},
    )
    assign_b = client.post(
        f"/api/admin/horarios/trabajadores/{worker_b_id}/asignar",
        json={
            "fecha_inicio": "2026-08-01",
            "hora_entrada": "09:00",
            "hora_salida_almuerzo": "13:45",
            "hora_regreso_almuerzo": "14:45",
            "hora_salida": "18:00",
            "tolerancia_entrada": 0,
            "tolerancia_regreso_almuerzo": 0,
        },
    )
    reassign_a = client.post(
        f"/api/admin/horarios/trabajadores/{worker_a_id}/asignar",
        json={
            "fecha_inicio": "2026-09-01",
            "hora_entrada": "09:00",
            "hora_salida_almuerzo": "13:45",
            "hora_regreso_almuerzo": "14:45",
            "hora_salida": "18:00",
            "tolerancia_entrada": 0,
            "tolerancia_regreso_almuerzo": 0,
        },
    )
    history_a = client.get(f"/api/admin/horarios/trabajadores/{worker_a_id}/historial")
    current_b = client.get(f"/api/admin/horarios/trabajadores/{worker_b_id}/actual")

    assert assign_a.status_code == 201
    assert assign_b.get_json()["data"]["horario"]["hora_entrada"] == "09:00"
    assert reassign_a.status_code == 201
    assert len(history_a.get_json()["data"]["historial"]) == 2
    assert current_b.get_json()["data"]["horario"]["hora_entrada"] == "09:00"

    with app.app_context():
        old_a = (
            HorarioTrabajador.query.filter_by(trabajador_id=worker_a_id, activo=False)
            .order_by(HorarioTrabajador.id.asc())
            .first()
        )
        assert old_a.fecha_fin == date(2026, 8, 31)
