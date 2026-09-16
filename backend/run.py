"""Modulo run del sistema de control de horarios.

Agrupa la logica propia necesaria para esta responsabilidad sin exponer detalles de infraestructura.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
