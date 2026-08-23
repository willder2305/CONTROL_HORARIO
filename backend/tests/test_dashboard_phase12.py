from datetime import date, datetime, time

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Administrador, HorarioTrabajador, Marcacion, Trabajador


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


def build_authenticated_client_with_dashboard_data():
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
        workers = [
            Trabajador(codigo="EMP-0001", nombre="Ana", apellido="Lopez", activo=True),
            Trabajador(codigo="EMP-0002", nombre="Luis", apellido="Mendez", activo=True),
            Trabajador(codigo="EMP-0003", nombre="Ines", apellido="Diaz", activo=True),
            Trabajador(codigo="EMP-0004", nombre="Baja", apellido="No", activo=False),
        ]
        db.session.add_all(workers)
        db.session.flush()
        schedules = []
        for worker in workers[:3]:
            schedules.append(
                HorarioTrabajador(
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
            )
        db.session.add_all(schedules)
        db.session.flush()
        today = date(2026, 8, 20)
        db.session.add_all(
            [
                Marcacion(
                    trabajador_id=workers[0].id,
                    fecha=today,
                    fecha_hora=datetime(2026, 8, 20, 8, 10),
                    tipo_marcacion="ENTRADA",
                    hora_programada=time(8, 0),
                    hora_real=time(8, 10),
                    estado="TARDANZA",
                    minutos_diferencia=10,
                    horario_trabajador_id=schedules[0].id,
                    origen="TEST",
                ),
                Marcacion(
                    trabajador_id=workers[0].id,
                    fecha=today,
                    fecha_hora=datetime(2026, 8, 20, 12, 45),
                    tipo_marcacion="SALIDA_ALMUERZO",
                    hora_programada=time(12, 45),
                    hora_real=time(12, 45),
                    estado="A_TIEMPO",
                    minutos_diferencia=0,
                    horario_trabajador_id=schedules[0].id,
                    origen="TEST",
                ),
                Marcacion(
                    trabajador_id=workers[1].id,
                    fecha=today,
                    fecha_hora=datetime(2026, 8, 20, 8, 0),
                    tipo_marcacion="ENTRADA",
                    hora_programada=time(8, 0),
                    hora_real=time(8, 0),
                    estado="A_TIEMPO",
                    minutos_diferencia=0,
                    horario_trabajador_id=schedules[1].id,
                    origen="TEST",
                ),
                Marcacion(
                    trabajador_id=workers[1].id,
                    fecha=today,
                    fecha_hora=datetime(2026, 8, 20, 13, 55),
                    tipo_marcacion="REGRESO_ALMUERZO",
                    hora_programada=time(13, 45),
                    hora_real=time(13, 55),
                    estado="TARDANZA",
                    minutos_diferencia=10,
                    horario_trabajador_id=schedules[1].id,
                    origen="TEST",
                ),
                Marcacion(
                    trabajador_id=workers[1].id,
                    fecha=today,
                    fecha_hora=datetime(2026, 8, 20, 18, 0),
                    tipo_marcacion="SALIDA",
                    hora_programada=time(18, 0),
                    hora_real=time(18, 0),
                    estado="A_TIEMPO",
                    minutos_diferencia=0,
                    horario_trabajador_id=schedules[1].id,
                    origen="TEST",
                ),
            ]
        )
        db.session.commit()

    client = app.test_client()
    client.post("/api/auth/login", json={"usuario": "admin", "password": "Correcta123"})
    return app, client


def test_dashboard_requires_session():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()

    response = app.test_client().get("/api/admin/marcaciones/dashboard?fecha=2026-08-20")

    assert response.status_code == 401


def test_dashboard_counts_expected_metrics():
    app, client = build_authenticated_client_with_dashboard_data()

    response = client.get("/api/admin/marcaciones/dashboard?fecha=2026-08-20")
    data = response.get_json()["data"]

    assert response.status_code == 200
    assert data["trabajadores_activos"] == 3
    assert data["presentes_hoy"] == 2
    assert data["entradas_registradas"] == 2
    assert data["tardanzas"] == 2
    assert data["en_almuerzo"] == 1
    assert data["regresos_tardios"] == 1
    assert data["salidas"] == 1
    assert data["pendientes_salida"] == 1
