"""Disponibilidad Service - Business logic for Disponibilidad and Excepciones."""

from collections.abc import Callable, Sequence
from datetime import date, datetime, time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException
from app.models.profesional import DiaSemana, ExcepcionDisponibilidad, TipoExcepcion
from app.models.turno import Turno
from app.repositories.disponibilidad_repo import DisponibilidadRepo
from app.repositories.excepcion_repo import ExcepcionRepo
from app.repositories.turno_repo import TurnoRepo
from app.schemas.profesional import (
    DisponibilidadCreate,
    DisponibilidadResponse,
    ExcepcionCreate,
    ExcepcionResponse,
    GrillaDisponibilidadResponse,
)

# Horario que rige una fecha: (inicio, fin), o None si ese día no se atiende
Horario = tuple[time, time] | None

MAX_FECHAS_EN_MENSAJE = 5


def _naive(dt: datetime) -> datetime:
    """Hora de reloj del negocio sin etiqueta (SQLite puede devolverla con o sin tz)."""
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


def _turnos_fuera_de_horario(
    turnos: Sequence[Turno], horario_de: Callable[[date], Horario]
) -> list[Turno]:
    """Turnos que no entran completos en el horario que regiría su fecha (CU-02)."""
    afuera = []
    for turno in turnos:
        inicio, fin = _naive(turno.fecha_inicio), _naive(turno.fecha_fin)
        horario = horario_de(inicio.date())
        if horario is None or fin.date() != inicio.date():
            afuera.append(turno)
            continue
        desde, hasta = horario
        if inicio.time() < desde or fin.time() > hasta:
            afuera.append(turno)
    return afuera


def _horario_de_excepcion(exc: ExcepcionDisponibilidad | ExcepcionCreate) -> Horario:
    tipo = exc.tipo.value if isinstance(exc.tipo, TipoExcepcion) else exc.tipo
    if tipo == TipoExcepcion.CERRADO.value or exc.hora_inicio is None or exc.hora_fin is None:
        return None
    return exc.hora_inicio, exc.hora_fin


def _conflicto(afuera: list[Turno]) -> ConflictException:
    fechas = ", ".join(_naive(t.fecha_inicio).strftime("%d/%m %H:%M") for t in afuera[:MAX_FECHAS_EN_MENSAJE])
    if len(afuera) > MAX_FECHAS_EN_MENSAJE:
        fechas += ", …"
    cantidad = "1 turno quedaría" if len(afuera) == 1 else f"{len(afuera)} turnos quedarían"
    return ConflictException(
        f"{cantidad} fuera de horario: {fechas}. Reasignalos o cancelalos antes de guardar."
    )


class DisponibilidadService:
    """Service layer for Disponibilidad and ExcepcionDisponibilidad business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.disp_repo = DisponibilidadRepo(session)
        self.exc_repo = ExcepcionRepo(session)
        self.turno_repo = TurnoRepo(session)

    # =========================================================================
    # Grilla semanal (Disponibilidad)
    # =========================================================================

    async def obtener_mi_grilla(self, profesional_id: int) -> GrillaDisponibilidadResponse:
        """Get complete weekly grid for a profesional."""
        from app.repositories.profesional_repo import ProfesionalRepo
        prof_repo = ProfesionalRepo(self.session)
        profesional = await prof_repo.get_by_id(profesional_id)

        if not profesional:
            raise ValueError("Profesional no encontrado")

        disponibilidades = await self.disp_repo.get_activa_by_profesional(profesional_id)

        return GrillaDisponibilidadResponse(
            profesional_id=profesional_id,
            slot_duracion_min=profesional.slot_duracion_min,
            grilla=[DisponibilidadResponse.model_validate(d) for d in disponibilidades]
        )

    async def actualizar_grilla_completa(
        self, profesional_id: int, grilla: list[DisponibilidadCreate]
    ) -> GrillaDisponibilidadResponse:
        """Bulk replace weekly grid for a profesional."""
        # Validate: max one per day
        dias_vistos = set()
        for d in grilla:
            if d.dia_semana in dias_vistos:
                raise ValueError(f"Día duplicado en grilla: {d.dia_semana}")
            dias_vistos.add(d.dia_semana)

        # No dejar turnos activos fuera del nuevo horario (las excepciones siguen mandando)
        turnos = await self.turno_repo.get_activos_futuros(profesional_id)
        if turnos:
            por_dia = {d.dia_semana: (d.hora_inicio, d.hora_fin) for d in grilla}
            dias = list(DiaSemana)
            fechas = [_naive(t.fecha_inicio).date() for t in turnos]
            excepciones = {
                e.fecha: _horario_de_excepcion(e)
                for e in await self.exc_repo.list_by_profesional(profesional_id, min(fechas), max(fechas))
            }

            def horario_de(fecha: date) -> Horario:
                if fecha in excepciones:
                    return excepciones[fecha]
                return por_dia.get(dias[fecha.weekday()].value)

            afuera = _turnos_fuera_de_horario(turnos, horario_de)
            if afuera:
                raise _conflicto(afuera)

        # Replace all
        nuevas = await self.disp_repo.replace_all_for_profesional(profesional_id, grilla)
        await self.session.commit()

        from app.repositories.profesional_repo import ProfesionalRepo
        prof_repo = ProfesionalRepo(self.session)
        profesional = await prof_repo.get_by_id(profesional_id)
        if not profesional:
            raise ValueError("Profesional no encontrado")

        return GrillaDisponibilidadResponse(
            profesional_id=profesional_id,
            slot_duracion_min=profesional.slot_duracion_min,
            grilla=[DisponibilidadResponse.model_validate(d) for d in nuevas]
        )

    # =========================================================================
    # Excepciones
    # =========================================================================

    async def obtener_excepciones(
        self, profesional_id: int, desde: date | None = None, hasta: date | None = None
    ) -> list[ExcepcionResponse]:
        """Get excepciones for a profesional with optional date range."""
        excepciones = await self.exc_repo.list_by_profesional(profesional_id, desde, hasta)
        return [ExcepcionResponse.model_validate(e) for e in excepciones]

    async def agregar_excepcion(
        self, profesional_id: int, data: ExcepcionCreate
    ) -> ExcepcionResponse:
        """Add excepcion for a profesional."""
        # Check if excepcion already exists for this date
        existing = await self.exc_repo.get_by_profesional_and_fecha(profesional_id, data.fecha)
        if existing:
            raise ValueError("Ya existe una excepción para esta fecha")

        # No dejar turnos activos de esa fecha fuera de la excepción
        turnos = [
            t for t in await self.turno_repo.get_activos_futuros(profesional_id)
            if _naive(t.fecha_inicio).date() == data.fecha
        ]
        horario = _horario_de_excepcion(data)
        afuera = _turnos_fuera_de_horario(turnos, lambda _fecha: horario)
        if afuera:
            raise _conflicto(afuera)

        excepcion = await self.exc_repo.create(profesional_id, data)
        await self.session.commit()
        await self.session.refresh(excepcion)
        return ExcepcionResponse.model_validate(excepcion)

    async def eliminar_excepcion(self, profesional_id: int, excepcion_id: int) -> bool:
        """Delete excepcion (ownership validated)."""
        excepcion = await self.exc_repo.get_by_id(excepcion_id)
        if not excepcion or excepcion.profesional_id != profesional_id:
            return False

        success = await self.exc_repo.delete(excepcion_id)
        if success:
            await self.session.commit()
        return success
