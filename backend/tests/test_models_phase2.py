from app import create_app, db


def test_phase_2_tables_are_registered():
    app = create_app()
    tables = set(db.metadata.tables.keys())

    assert {
        "administradores",
        "trabajadores",
        "plantillas_horario",
        "horarios_trabajadores",
        "huellas",
        "marcaciones",
        "auditoria",
    }.issubset(tables)


def test_marcaciones_has_unique_worker_date_type_constraint():
    constraints = db.metadata.tables["marcaciones"].constraints
    constraint_names = {constraint.name for constraint in constraints}

    assert "uq_marcacion_trabajador_fecha_tipo" in constraint_names
