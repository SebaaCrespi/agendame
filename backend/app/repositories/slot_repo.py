"""Slot Repository - Core logic for generating available slots."""

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutils import ahora_negocio
from app.models.profesional import (
    DiaSemana,
    Disponibilidad,
    ExcepcionDisponibilidad,
    Profesional,
    TipoExcepcion,
)
from app.models.turno import Turno, TurnoEstado


class SlotRepo:
    """Repository for slot generation logic."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_slots_disponibles(
        self,
        profesional_id: int,
        desde: date,
        hasta: date,
        duracion_min: int | None = None,
        excluir_turno_id: int | None = None,
    ) -> list[dict[str, object]]:
        """
        Core algorithm: Generate available slots for a profesional in date range.

        Algorithm:
        1. Get profesional (for slot_duracion_min)
        2. Get active grilla semanal (disponibilidades)
        3. Get excepciones in range
        4. Get turnos ocupados in range (CONFIRMADO, PENDIENTE, EN_CURSO)
        5. Expand grilla to date range, apply excepciones, generate slots, filter occupied
        """
        # 1. Get profesional
        profesional = await self.session.get(Profesional, profesional_id)
        if not profesional or not profesional.activo:
            return []

        slot_duracion = profesional.slot_duracion_min

        # 2. Get active grilla semanal
        grilla = await self._get_active_grilla(profesional_id)
        if not grilla:
            return []

        # 3. Get excepciones in range
        excepciones = await self._get_excepciones_in_range(profesional_id, desde, hasta)

        # 4. Get turnos ocupados in range
        turnos_ocupados = await self._get_turnos_ocupados(profesional_id, desde, hasta, excluir_turno_id)

        # 5. Generate slots
        return self._generate_slots(
            grilla=grilla,
            excepciones=excepciones,
            turnos_ocupados=turnos_ocupados,
            slot_duracion_min=slot_duracion,
            desde=desde,
            hasta=hasta,
            duracion_min=duracion_min or slot_duracion,
        )

    async def _get_active_grilla(self, profesional_id: int) -> list[Disponibilidad]:
        """Get active disponibilidades for a profesional."""
        stmt = select(Disponibilidad).where(
            Disponibilidad.profesional_id == profesional_id,
            Disponibilidad.activo
        ).order_by(Disponibilidad.dia_semana)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _get_excepciones_in_range(
        self, profesional_id: int, desde: date, hasta: date
    ) -> list[ExcepcionDisponibilidad]:
        """Get excepciones for a profesional in date range."""
        stmt = select(ExcepcionDisponibilidad).where(
            ExcepcionDisponibilidad.profesional_id == profesional_id,
            ExcepcionDisponibilidad.fecha >= desde,
            ExcepcionDisponibilidad.fecha <= hasta
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _get_turnos_ocupados(
        self, profesional_id: int, desde: date, hasta: date, excluir_turno_id: int | None = None
    ) -> list[Turno]:
        """Get turnos that block slots (CONFIRMADO, PENDIENTE, EN_CURSO), except `excluir_turno_id`."""
        # Convert dates to datetime for comparison
        desde_dt = datetime.combine(desde, time.min).replace(tzinfo=UTC)
        hasta_dt = datetime.combine(hasta, time.max).replace(tzinfo=UTC)

        stmt = select(Turno).where(
            Turno.profesional_id == profesional_id,
            Turno.estado.in_([
                TurnoEstado.CONFIRMADO,
                TurnoEstado.PENDIENTE,
                TurnoEstado.EN_CURSO
            ]),
            Turno.fecha_inicio >= desde_dt,
            Turno.fecha_inicio <= hasta_dt
        )
        if excluir_turno_id is not None:
            stmt = stmt.where(Turno.id != excluir_turno_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _generate_slots(
        self,
        grilla: list[Disponibilidad],
        excepciones: list[ExcepcionDisponibilidad],
        turnos_ocupados: list[Turno],
        slot_duracion_min: int,
        desde: date,
        hasta: date,
        duracion_min: int | None = None,
    ) -> list[dict[str, object]]:
        """
        Generate slots from grilla, applying excepciones and filtering occupied slots.

        Returns list of dicts: {fecha, hora_inicio, hora_fin, disponible}
        """
        # Convert excepciones to dict for quick lookup
        exc_dict: dict[date, dict[str, object]] = {}
        for exc_item in excepciones:
            if exc_item.tipo == TipoExcepcion.CERRADO:
                exc_dict[exc_item.fecha] = {"tipo": "CERRADO"}
            else:  # HORARIO_ESPECIAL
                exc_dict[exc_item.fecha] = {
                    "tipo": "HORARIO_ESPECIAL",
                    "hora_inicio": exc_item.hora_inicio,
                    "hora_fin": exc_item.hora_fin
                }

        # Convert turnos to list of (start, end) tuples for quick check
        turnos_ranges = []
        for turno in turnos_ocupados:
            # Ensure timezone-aware for comparison
            inicio = turno.fecha_inicio
            fin = turno.fecha_fin
            if inicio.tzinfo is None:
                inicio = inicio.replace(tzinfo=UTC)
            if fin.tzinfo is None:
                fin = fin.replace(tzinfo=UTC)
            turnos_ranges.append((inicio, fin))

        # Los inicios avanzan de a slot_duracion_min (granularidad); cada slot cubre
        # la duración del turno a reservar (la del servicio, si se indicó).
        duracion = timedelta(minutes=duracion_min or slot_duracion_min)
        ahora = ahora_negocio()

        slots = []
        current_date = desde

        while current_date <= hasta:
            # Get day of week (0=Monday, 6=Sunday)
            dia_semana_num = current_date.weekday()
            dia_semana = DiaSemana(list(DiaSemana)[dia_semana_num].value)

            # Find disponibilidad for this day
            disp = next((d for d in grilla if d.dia_semana == dia_semana), None)

            if disp:
                # Check if there's an excepcion for this date
                exc = exc_dict.get(current_date)

                if exc and exc["tipo"] == "CERRADO":
                    # Day is closed, no slots
                    pass
                else:
                    # Determine effective hours
                    if exc and exc["tipo"] == "HORARIO_ESPECIAL":
                        hora_inicio = exc["hora_inicio"]
                        hora_fin = exc["hora_fin"]
                        assert isinstance(hora_inicio, time)
                        assert isinstance(hora_fin, time)
                    else:
                        hora_inicio = disp.hora_inicio
                        hora_fin = disp.hora_fin

                    # Generate base slots
                    current_dt = datetime.combine(current_date, hora_inicio).replace(tzinfo=UTC)
                    fin_dt = datetime.combine(current_date, hora_fin).replace(tzinfo=UTC)
                    slot_delta = timedelta(minutes=slot_duracion_min)

                    while current_dt + duracion <= fin_dt:
                        slot_inicio = current_dt
                        slot_fin = current_dt + duracion

                        # Pasado (hora del negocio) o solapado con un turno activo -> no disponible
                        disponible = slot_inicio > ahora
                        for t_inicio, t_fin in turnos_ranges if disponible else []:
                            # Check overlap: slot_inicio < t_fin AND slot_fin > t_inicio
                            if slot_inicio < t_fin and slot_fin > t_inicio:
                                disponible = False
                                break

                        slots.append({
                            "fecha": current_date,
                            "hora_inicio": slot_inicio.time(),
                            "hora_fin": slot_fin.time(),
                            "disponible": disponible
                        })

                        current_dt += slot_delta

            current_date += timedelta(days=1)

        return slots

    async def get_slots_count(
        self,
        profesional_id: int,
        desde: date,
        hasta: date,
    ) -> int:
        """Get total count of available slots (for pagination metadata)."""
        slots = await self.get_slots_disponibles(profesional_id, desde, hasta)
        return len([s for s in slots if s["disponible"]])
