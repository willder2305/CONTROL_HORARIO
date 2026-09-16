"""Punto de entrada de Flask configurable para ejecucion local o servidor.

Lee host, puerto y depuracion desde variables de entorno sin fijar valores de produccion en codigo.
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    app.run(host=host, port=port, debug=debug)
