"""
Herramientas del chatbot (CU-05/06).

Cada herramienta usa los servicios existentes, con sus validaciones. El cliente de
las reservas y cancelaciones se captura de la sesión al crear las herramientas: el
modelo no lo recibe ni lo puede elegir.
"""

import json
import logging
from datetime import date, datetime, time, timedelta
from typing import Any

from langchain_core.tools import BaseTool, tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.timeutils import ahora_negocio
from app.schemas.turno import MomentoTurno, TurnoFiltros
from app.services.profesional_service import ProfesionalService
from app.services.turno_service import TurnoService

logger = logging.getLogger(__name__)

MAX_DIAS_CONSULTA = 14
SIN_SESION = "Necesitás iniciar sesión como cliente para eso. Podés hacerlo desde «Iniciar sesión»."

ACCION_RESERVA = "turno_reservado"
ACCION_CANCELACION = "turno_cancelado"

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def hhmm(t: time) -> str:
    return t.strftime("%H:%M")


def fecha_texto(d: date, anio_actual: int | None = None) -> str:
    """'sábado 7 de noviembre' para mostrarle al cliente; agrega el año si no es el actual."""
    anio_actual = ahora_negocio().year if anio_actual is None else anio_actual
    texto = f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]}"
    return texto if d.year == anio_actual else f"{texto} de {d.year}"


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _fecha(valor: str) -> date:
    return date.fromisoformat(valor.strip())


def _hora(valor: str) -> time:
    return time.fromisoformat(valor.strip()[:5])


def crear_herramientas(session: AsyncSession, cliente_id: int | None, acciones: list[str]) -> list[BaseTool]:
    """
    Herramientas para una conversación.

    `cliente_id` es el de la sesión (None si no hay cliente logueado).
    `acciones` se completa con lo que cambió, para que el frontend se refresque.
    """
    turnos = TurnoService(session)
    profesionales = ProfesionalService(session)

    async def _ejecutar(nombre: str, fn: Any) -> str:
        try:
            return str(await fn())
        except AppException as e:
            logger.info("chat tool %s rechazada: %s", nombre, e.status_code)
            return f"Error: {e.detail}"
        except ValueError as e:
            return f"Error: {e}"

    @tool
    async def buscar_profesionales(nombre: str | None = None) -> str:
        """Busca profesionales activos por nombre (o todos si no se indica). Devuelve id, nombre y sus servicios con id, duración en minutos y precio en pesos."""

        async def fn() -> str:
            encontrados = await profesionales.listar_activos(q=nombre.strip() if nombre else None)
            nota = ""
            if nombre and not encontrados:
                encontrados = await profesionales.listar_activos()
                nota = f"No hay ningún profesional llamado «{nombre}». Estos son los activos: "
            datos = [
                {
                    "id": p.id,
                    "nombre": f"{p.nombre} {p.apellido}",
                    "servicios": [
                        {"id": s.id, "nombre": s.nombre, "duracion_min": s.duracion_min, "precio_pesos": s.precio / 100}
                        for s in p.servicios
                        if s.activo
                    ],
                }
                for p in encontrados
            ]
            return nota + _json(datos)

        return await _ejecutar("buscar_profesionales", fn)

    @tool
    async def consultar_disponibilidad(profesional_id: int, servicio_id: int, desde: str, hasta: str | None = None) -> str:
        """Horarios libres de un profesional para un servicio. `desde` y `hasta` en formato AAAA-MM-DD (hasta 14 días; si no se indica `hasta`, es el mismo día). Devuelve, por fecha AAAA-MM-DD, el día escrito para mostrarle al cliente (`dia`) y las horas de inicio libres en formato HH:MM (`horas`)."""

        async def fn() -> str:
            inicio = _fecha(desde)
            fin = _fecha(hasta) if hasta else inicio
            if fin < inicio:
                raise ValueError("la fecha final es anterior a la inicial")
            if (fin - inicio).days >= MAX_DIAS_CONSULTA:
                fin = inicio + timedelta(days=MAX_DIAS_CONSULTA - 1)
            disp = await turnos.consultar_disponibilidad(profesional_id, servicio_id, inicio, fin)
            if not disp.profesionales:
                return "Error: el profesional no existe, está inactivo o no ofrece ese servicio"
            libres = {
                fecha: [hhmm(s.hora_inicio) for s in slots if s.disponible]
                for fecha, slots in disp.profesionales[0].slots_por_fecha.items()
            }
            libres = {f: h for f, h in libres.items() if h}
            if not libres:
                return "No hay horarios libres en esas fechas (puede que no atienda esos días o que esté todo ocupado)."
            return _json({str(f): {"dia": fecha_texto(_fecha(str(f))), "horas": h} for f, h in libres.items()})

        return await _ejecutar("consultar_disponibilidad", fn)

    @tool
    async def reservar_turno(profesional_id: int, servicio_id: int, fecha: str, hora: str) -> str:
        """Reserva un turno para el cliente de la sesión. Usar SOLO después de que el cliente confirmó profesional, servicio, fecha (AAAA-MM-DD) y hora (HH:MM)."""
        if cliente_id is None:
            return SIN_SESION

        async def fn() -> str:
            t = await turnos.crear_reserva_manual(cliente_id, profesional_id, servicio_id, _fecha(fecha), _hora(hora))
            acciones.append(ACCION_RESERVA)
            logger.info("chat reservó turno %s", t.id)
            return _json(
                {
                    "turno_id": t.id,
                    "estado": t.estado,
                    "profesional": t.profesional_nombre,
                    "servicio": t.servicio_nombre,
                    "fecha": t.fecha_inicio.date().isoformat(),
                    "dia": fecha_texto(t.fecha_inicio.date()),
                    "hora_inicio": hhmm(t.fecha_inicio.time()),
                    "hora_fin": hhmm(t.fecha_fin.time()),
                }
            )

        return await _ejecutar("reservar_turno", fn)

    @tool
    async def mis_turnos() -> str:
        """Próximos turnos del cliente de la sesión (id, fecha, hora, profesional, servicio y estado)."""
        if cliente_id is None:
            return SIN_SESION

        async def fn() -> str:
            items, _ = await turnos.get_turnos_by_cliente(
                cliente_id, TurnoFiltros(momento=MomentoTurno.PROXIMOS, page=1, size=10)
            )
            if not items:
                return "El cliente no tiene turnos próximos."
            return _json(
                [
                    {
                        "turno_id": t.id,
                        "fecha": t.fecha_inicio.date().isoformat(),
                        "dia": fecha_texto(t.fecha_inicio.date()),
                        "hora": hhmm(t.fecha_inicio.time()),
                        "profesional": t.profesional_nombre,
                        "servicio": t.servicio_nombre,
                        "estado": t.estado,
                    }
                    for t in items
                ]
            )

        return await _ejecutar("mis_turnos", fn)

    @tool
    async def cancelar_turno(turno_id: int, motivo: str = "") -> str:
        """Cancela un turno del cliente de la sesión. Usar SOLO después de mostrarle al cliente qué turno se va a cancelar y de que responda que sí en un mensaje posterior. `motivo`: si en algún mensaje de la conversación el cliente dijo por qué cancela, pasalo SIEMPRE con sus palabras (por ejemplo "no voy a poder ir"); si no dijo nada, dejalo vacío y no se lo pidas. Solo se puede con más de 2 horas de antelación."""
        if cliente_id is None:
            return SIN_SESION

        async def fn() -> str:
            texto = (motivo or "").strip()[:500] or "Cancelado desde el chat"
            t = await turnos.cancelar_turno_cliente(turno_id, cliente_id, texto)
            acciones.append(ACCION_CANCELACION)
            logger.info("chat canceló turno %s", t.id)
            return _json({"turno_id": t.id, "estado": t.estado})

        return await _ejecutar("cancelar_turno", fn)

    return [buscar_profesionales, consultar_disponibilidad, reservar_turno, mis_turnos, cancelar_turno]


def hoy_texto(ahora: datetime) -> str:
    """'jueves 2026-11-05' para el system prompt."""
    return f"{DIAS[ahora.weekday()]} {ahora.date().isoformat()}"
