from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from app import db
from app.models import HorarioTrabajador, Huella, Marcacion
from app.services.fingerprint import get_fingerprint_provider
from app.services.fingerprint.real_provider import FingerprintDeviceError
from app.utils.datetime_utils import obtener_hora_actual

TIPO_ENTRADA = "ENTRADA"
TIPO_SALIDA_ALMUERZO = "SALIDA_ALMUERZO"
TIPO_REGRESO_ALMUERZO = "REGRESO_ALMUERZO"
TIPO_SALIDA = "SALIDA"

TIPOS_MARCACION = (
    TIPO_ENTRADA,
    TIPO_SALIDA_ALMUERZO,
    TIPO_REGRESO_ALMUERZO,
    TIPO_SALIDA,
)

SECUENCIA_MARCACIONES = (
    TIPO_ENTRADA,
    TIPO_SALIDA_ALMUERZO,
    TIPO_REGRESO_ALMUERZO,
    TIPO_SALIDA,
)

TIPO_MARCACION_TEXTO = {
    TIPO_ENTRADA: "Entrada",
    TIPO_SALIDA_ALMUERZO: "Salida de almuerzo",
    TIPO_REGRESO_ALMUERZO: "Entrada de almuerzo",
    TIPO_SALIDA: "Salida",
}

ESTADO_A_TIEMPO = "A_TIEMPO"
ESTADO_TARDANZA = "TARDANZA"
ESTADO_ANTICIPADO = "ANTICIPADO"
ESTADO_SALIDA_ANTICIPADA = "SALIDA_ANTICIPADA"
MARCACION_COOLDOWN_SECONDS = 30


@dataclass
class ResultadoValidacion:
    valido: bool
    code: str
    message: str


def serialize_time(value):
    return value.strftime("%H:%M") if value else None


def serialize_worker(worker):
    return {
        "id": worker.id,
        "codigo": worker.codigo,
        "nombre": worker.nombre,
        "apellido": worker.apellido,
        "activo": worker.activo,
    }


def serialize_mark(mark):
    return {
        "id": mark.id,
        "trabajador": serialize_worker(mark.trabajador),
        "fecha": mark.fecha.isoformat(),
        "tipo": mark.tipo_marcacion,
        "tipo_marcacion": mark.tipo_marcacion,
        "tipoMarcacion": mark.tipo_marcacion,
        "tipoMarcacionTexto": TIPO_MARCACION_TEXTO.get(mark.tipo_marcacion, mark.tipo_marcacion),
        "hora": mark.hora_real.strftime("%I:%M %p"),
        "horaRegistrada": mark.hora_real.strftime("%I:%M %p"),
        "hora_24": serialize_time(mark.hora_real),
        "hora_programada": serialize_time(mark.hora_programada),
        "estado": mark.estado,
        "minutos_diferencia": mark.minutos_diferencia,
    }


def obtener_marcaciones_dia(trabajador_id, fecha):
    """
    Obtiene las marcaciones existentes de un trabajador para una fecha.

    Recibe:
        trabajador_id y fecha.

    Utilizado desde:
        Motor de asistencia y futuras rutas de marcacion.

    Retorna:
        Diccionario indexado por tipo_marcacion.
    """
    marcaciones = Marcacion.query.filter_by(
        trabajador_id=trabajador_id,
        fecha=fecha,
    ).all()
    return {marcacion.tipo_marcacion: marcacion for marcacion in marcaciones}


def obtener_horario_activo(trabajador_id, fecha):
    return (
        HorarioTrabajador.query.filter(
            HorarioTrabajador.trabajador_id == trabajador_id,
            HorarioTrabajador.fecha_inicio <= fecha,
            (HorarioTrabajador.fecha_fin.is_(None)) | (HorarioTrabajador.fecha_fin >= fecha),
        )
        .order_by(HorarioTrabajador.fecha_inicio.desc(), HorarioTrabajador.id.desc())
        .first()
    )


def obtener_horario_trabajador(trabajador_id, fecha):
    """
    Obtiene el horario vigente de un trabajador para una fecha.

    Recibe:
        trabajador_id y fecha.

    Utilizado desde:
        Motor de puntualidad y futuro registro completo de marcaciones.

    Retorna:
        HorarioTrabajador vigente o None.
    """
    return obtener_horario_activo(trabajador_id, fecha)


def trabajador_tiene_almuerzo(horario):
    return bool(
        horario
        and horario.hora_salida_almuerzo is not None
        and horario.hora_regreso_almuerzo is not None
    )


def construir_secuencia_marcaciones(horario):
    if not horario:
        return ()
    if trabajador_tiene_almuerzo(horario):
        return SECUENCIA_MARCACIONES
    return (TIPO_ENTRADA, TIPO_SALIDA)


def determinar_siguiente_marcacion(trabajador, fecha):
    horario = obtener_horario_activo(trabajador.id, fecha)
    if not horario:
        return {
            "success": False,
            "code": "HORARIO_NO_ASIGNADO",
            "message": "No se puede realizar la marcacion. No tiene un horario asignado para esta jornada.",
        }

    secuencia = construir_secuencia_marcaciones(horario)
    marcaciones_dia = obtener_marcaciones_dia(trabajador.id, fecha)
    for tipo_marcacion in secuencia:
        if tipo_marcacion not in marcaciones_dia:
            return {
                "success": True,
                "tipo_marcacion": tipo_marcacion,
                "horario": horario,
                "marcaciones_dia": marcaciones_dia,
                "secuencia": secuencia,
            }

    return {
        "success": False,
        "code": "JORNADA_COMPLETADA",
        "message": "Jornada completada. Ya se registraron todas las marcaciones correspondientes a esta jornada.",
    }


def validar_duplicado(tipo_marcacion, marcaciones_dia):
    if tipo_marcacion not in marcaciones_dia:
        return ResultadoValidacion(True, "OK", "No existe marcacion duplicada.")

    marcacion = marcaciones_dia[tipo_marcacion]
    hora = marcacion.hora_real.strftime("%H:%M") if marcacion.hora_real else ""
    return ResultadoValidacion(
        False,
        "MARCACION_DUPLICADA",
        f"Ya existe una marcacion {tipo_marcacion} registrada hoy a las {hora}.",
    )


def validar_secuencia(trabajador_id, tipo_marcacion, fecha):
    """
    Valida si el trabajador puede realizar la marcacion solicitada.

    Reglas:
        ENTRADA -> SALIDA_ALMUERZO -> REGRESO_ALMUERZO -> SALIDA.

    Recibe:
        trabajador_id, tipo_marcacion y fecha.

    Utilizado desde:
        services/attendance_service.py y futuras rutas de marcacion.

    Retorna:
        ResultadoValidacion con estado, codigo y mensaje.
    """
    if tipo_marcacion not in TIPOS_MARCACION:
        return ResultadoValidacion(
            False,
            "TIPO_MARCACION_INVALIDO",
            "Tipo de marcacion no permitido.",
        )

    marcaciones_dia = obtener_marcaciones_dia(trabajador_id, fecha)
    duplicado = validar_duplicado(tipo_marcacion, marcaciones_dia)
    if not duplicado.valido:
        return duplicado

    tiene_entrada = TIPO_ENTRADA in marcaciones_dia
    tiene_salida_almuerzo = TIPO_SALIDA_ALMUERZO in marcaciones_dia
    tiene_regreso_almuerzo = TIPO_REGRESO_ALMUERZO in marcaciones_dia
    horario = obtener_horario_activo(trabajador_id, fecha)
    secuencia = construir_secuencia_marcaciones(horario)
    tiene_almuerzo = trabajador_tiene_almuerzo(horario)

    if tipo_marcacion not in secuencia:
        return ResultadoValidacion(
            False,
            "TIPO_NO_CONFIGURADO_EN_HORARIO",
            "El horario asignado no contempla ese tipo de marcacion.",
        )

    if tipo_marcacion == TIPO_ENTRADA:
        return ResultadoValidacion(True, "OK", "Entrada permitida.")

    if tipo_marcacion == TIPO_SALIDA_ALMUERZO and not tiene_entrada:
        return ResultadoValidacion(
            False,
            "SECUENCIA_INVALIDA",
            "No puede registrar salida a almuerzo porque aun no ha marcado su entrada.",
        )

    if tipo_marcacion == TIPO_REGRESO_ALMUERZO:
        if not tiene_entrada:
            return ResultadoValidacion(
                False,
                "SECUENCIA_INVALIDA",
                "No puede registrar regreso de almuerzo porque aun no ha marcado su entrada.",
            )
        if not tiene_salida_almuerzo:
            return ResultadoValidacion(
                False,
                "SECUENCIA_INVALIDA",
                "No puede registrar regreso de almuerzo porque aun no ha marcado su salida a almuerzo.",
            )

    if tipo_marcacion == TIPO_SALIDA:
        if not tiene_entrada:
            return ResultadoValidacion(
                False,
                "SECUENCIA_INVALIDA",
                "No puede registrar salida porque no existe una entrada registrada para hoy.",
            )
        if tiene_almuerzo and not (tiene_salida_almuerzo and tiene_regreso_almuerzo):
            return ResultadoValidacion(
                False,
                "SECUENCIA_INVALIDA",
                "No puede registrar salida porque aun no ha completado su almuerzo.",
            )

    return ResultadoValidacion(True, "OK", "Marcacion permitida.")


def obtener_proxima_marcacion(trabajador_id, fecha):
    marcaciones_dia = obtener_marcaciones_dia(trabajador_id, fecha)
    horario = obtener_horario_activo(trabajador_id, fecha)
    for tipo_marcacion in construir_secuencia_marcaciones(horario):
        if tipo_marcacion not in marcaciones_dia:
            return tipo_marcacion
    return None


def obtener_hora_programada(horario, tipo_marcacion):
    """
    Retorna la hora esperada segun el tipo de marcacion.

    Recibe:
        HorarioTrabajador y tipo_marcacion.

    Utilizado desde:
        calculo de puntualidad y futuro guardado de marcaciones.

    Retorna:
        time correspondiente al horario asignado.
    """
    mapping = {
        TIPO_ENTRADA: horario.hora_entrada,
        TIPO_SALIDA_ALMUERZO: horario.hora_salida_almuerzo,
        TIPO_REGRESO_ALMUERZO: horario.hora_regreso_almuerzo,
        TIPO_SALIDA: horario.hora_salida,
    }
    return mapping.get(tipo_marcacion)


def calcular_diferencia_minutos(hora_real, hora_programada):
    real_minutes = hora_real.hour * 60 + hora_real.minute
    scheduled_minutes = hora_programada.hour * 60 + hora_programada.minute
    return real_minutes - scheduled_minutes


def calcular_estado(tipo_marcacion, hora_real, hora_programada, horario):
    """
    Calcula estado de puntualidad contra el horario individual asignado.

    Recibe:
        tipo_marcacion, hora_real, hora_programada y horario.

    Utilizado desde:
        Motor de puntualidad.

    Retorna:
        Tupla (estado, minutos_diferencia).
    """
    diferencia = calcular_diferencia_minutos(hora_real, hora_programada)

    if tipo_marcacion == TIPO_ENTRADA:
        limite = horario.tolerancia_entrada or 0
        if diferencia <= limite:
            return ESTADO_A_TIEMPO, 0
        return ESTADO_TARDANZA, diferencia - limite

    if tipo_marcacion == TIPO_SALIDA_ALMUERZO:
        if diferencia < 0:
            return ESTADO_ANTICIPADO, abs(diferencia)
        return ESTADO_A_TIEMPO, diferencia

    if tipo_marcacion == TIPO_REGRESO_ALMUERZO:
        limite = horario.tolerancia_regreso_almuerzo or 0
        if diferencia <= limite:
            return ESTADO_A_TIEMPO, 0
        return ESTADO_TARDANZA, diferencia - limite

    if tipo_marcacion == TIPO_SALIDA:
        if diferencia < 0:
            return ESTADO_SALIDA_ANTICIPADA, abs(diferencia)
        return ESTADO_A_TIEMPO, 0

    return ESTADO_A_TIEMPO, 0


def preparar_datos_puntualidad(trabajador_id, tipo_marcacion, fecha_hora=None):
    """
    Prepara los campos de puntualidad que posteriormente se guardaran.

    Recibe:
        trabajador_id, tipo_marcacion y fecha_hora opcional solo para pruebas.

    Utilizado desde:
        Fase 9 y futuro registro completo de marcaciones.

    Retorna:
        Diccionario con horario, fecha, hora real, programada, estado y diferencia.
    """
    fecha_hora_real = fecha_hora or obtener_hora_actual()
    fecha = fecha_hora_real.date()
    horario = obtener_horario_trabajador(trabajador_id, fecha)
    if not horario:
        return {
            "success": False,
            "code": "HORARIO_NO_ASIGNADO",
            "message": "El trabajador no tiene horario asignado para la fecha.",
        }

    hora_programada = obtener_hora_programada(horario, tipo_marcacion)
    if not hora_programada:
        return {
            "success": False,
            "code": "HORA_PROGRAMADA_NO_DISPONIBLE",
            "message": "No existe hora programada para el tipo de marcacion.",
        }

    hora_real = fecha_hora_real.time().replace(microsecond=0)
    estado, minutos_diferencia = calcular_estado(
        tipo_marcacion,
        hora_real,
        hora_programada,
        horario,
    )

    return {
        "success": True,
        "horario": horario,
        "horario_trabajador_id": horario.id,
        "fecha": fecha,
        "fecha_hora": fecha_hora_real,
        "hora_programada": hora_programada,
        "hora_real": hora_real,
        "estado": estado,
        "minutos_diferencia": minutos_diferencia,
    }


def identificar_trabajador_por_huella(fingerprint_id):
    provider = get_fingerprint_provider()
    active_fingerprints = Huella.query.filter_by(activa=True).all()
    fingerprint = provider.identify(fingerprint_id, active_fingerprints)
    if not fingerprint or not fingerprint.trabajador:
        return {
            "success": False,
            "code": "HUELLA_NO_RECONOCIDA",
            "message": "Huella no reconocida.",
        }
    if not fingerprint.trabajador.activo:
        return {
            "success": False,
            "code": "TRABAJADOR_INACTIVO",
            "message": "El trabajador identificado esta inactivo.",
        }
    return {"success": True, "trabajador": fingerprint.trabajador}


def registrar_marcacion_biometrica(tipo_marcacion=None, fingerprint_id=None, fecha_hora=None):
    """
    Registra una marcacion completa desde identificacion biometrica.

    Recibe:
        fingerprint_id opcional para proveedor mock y fecha_hora opcional solo para pruebas.
        tipo_marcacion se conserva por compatibilidad interna, pero no decide la funcion.

    Utilizado desde:
        POST /api/marcaciones/biometrica.

    Retorna:
        Diccionario de resultado con marcacion serializada o error de validacion.
    """
    try:
        identification = identificar_trabajador_por_huella(fingerprint_id)
    except ValueError as error:
        return {
            "success": False,
            "code": "HUELLA_INVALIDA",
            "message": str(error),
        }
    except FingerprintDeviceError as error:
        return {
            "success": False,
            "code": "LECTOR_NO_DISPONIBLE",
            "message": str(error),
        }

    if not identification["success"]:
        return identification

    trabajador = identification["trabajador"]
    fecha_hora_real = fecha_hora or obtener_hora_actual()
    fecha = fecha_hora_real.date()

    Trabajador = type(trabajador)
    trabajador_bloqueado = (
        Trabajador.query.filter_by(id=trabajador.id)
        .with_for_update()
        .first()
    )
    if not trabajador_bloqueado:
        return {
            "success": False,
            "code": "TRABAJADOR_NO_ENCONTRADO",
            "message": "No se puede realizar la marcacion. Consulte con el administrador.",
        }

    recent_mark = (
        Marcacion.query.filter(
            Marcacion.trabajador_id == trabajador_bloqueado.id,
            Marcacion.fecha_hora >= fecha_hora_real - timedelta(seconds=MARCACION_COOLDOWN_SECONDS),
            Marcacion.fecha_hora <= fecha_hora_real,
        )
        .order_by(Marcacion.fecha_hora.desc(), Marcacion.id.desc())
        .first()
    )
    if recent_mark:
        db.session.rollback()
        return {
            "success": False,
            "code": "MARCACION_RECIENTE",
            "message": "La marcacion ya se esta procesando. Intente nuevamente en unos segundos.",
        }

    next_mark = determinar_siguiente_marcacion(trabajador_bloqueado, fecha)
    if not next_mark["success"]:
        db.session.rollback()
        return next_mark

    tipo_marcacion = next_mark["tipo_marcacion"]
    sequence = validar_secuencia(trabajador_bloqueado.id, tipo_marcacion, fecha)
    if not sequence.valido:
        db.session.rollback()
        return {
            "success": False,
            "code": sequence.code,
            "message": sequence.message,
        }

    punctuality = preparar_datos_puntualidad(
        trabajador_bloqueado.id,
        tipo_marcacion,
        fecha_hora_real,
    )
    if not punctuality["success"]:
        db.session.rollback()
        return punctuality

    mark = Marcacion(
        trabajador_id=trabajador_bloqueado.id,
        fecha=punctuality["fecha"],
        fecha_hora=punctuality["fecha_hora"],
        tipo_marcacion=tipo_marcacion,
        hora_programada=punctuality["hora_programada"],
        hora_real=punctuality["hora_real"],
        estado=punctuality["estado"],
        minutos_diferencia=punctuality["minutos_diferencia"],
        horario_trabajador_id=punctuality["horario_trabajador_id"],
        origen="BIOMETRIA",
    )
    db.session.add(mark)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "success": False,
            "code": "MARCACION_DUPLICADA",
            "message": "Ya existe una marcacion de ese tipo para hoy.",
        }

    return {
        "success": True,
        "message": "Marcacion registrada correctamente.",
        "data": {
            "marcacion": serialize_mark(mark),
            "tipoMarcacion": mark.tipo_marcacion,
            "tipoMarcacionTexto": TIPO_MARCACION_TEXTO.get(mark.tipo_marcacion, mark.tipo_marcacion),
            "horaRegistrada": mark.hora_real.strftime("%I:%M %p"),
        },
    }
