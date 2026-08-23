from datetime import datetime
from zoneinfo import ZoneInfo

GUATEMALA_TZ = ZoneInfo("America/Guatemala")


def obtener_hora_actual():
    """
    Obtiene la fecha y hora actual del servidor en zona horaria de Guatemala.

    Recibe:
        No recibe parametros.

    Utilizado desde:
        Rutas y servicios que necesiten hora oficial del backend.

    Retorna:
        datetime timezone-aware con America/Guatemala.
    """
    return datetime.now(GUATEMALA_TZ)
