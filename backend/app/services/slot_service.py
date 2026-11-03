"""Slot Service - Core business logic for generating available slots."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.profesional_repo import ProfesionalRepo
from app.repositories.slot_repo import SlotRepo
from app.schemas.profesional import SlotResponse, SlotsListResponse


class SlotService:
    """Service layer for slot generation business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.slot_repo = SlotRepo(session)
        self.prof_repo = ProfesionalRepo(session)

    async def generar_slots_disponibles(
        self,
        profesional_id: int,
        desde: date,
        hasta: date,
        duracion_min: int | None = None,
    ) -> SlotsListResponse:
        """
        Generate available slots for a profesional in date range.

        This is the core business logic that:
        1. Validates profesional exists and is active
        2. Gets grilla semanal, excepciones, turnos ocupados
        3. Generates slots deterministically
        4. Returns formatted response
        """
        # Validate profesional
        profesional = await self.prof_repo.get_by_id(profesional_id)
        if not profesional:
            raise ValueError("Profesional no encontrado")
        if not profesional.activo:
            raise ValueError("Profesional inactivo")

        # Validate date range
        if desde > hasta:
            raise ValueError("Fecha 'desde' debe ser anterior o igual a 'hasta'")

        # Limit range to 60 days max (performance)
        if (hasta - desde).days > 60:
            raise ValueError("Rango máximo de 60 días")

        # Generate slots
        slots_data = await self.slot_repo.get_slots_disponibles(
            profesional_id=profesional_id,
            desde=desde,
            hasta=hasta,
            duracion_min=duracion_min,
        )

        # Convert to response models
        slots = [SlotResponse.model_validate(s) for s in slots_data]
        disponibles = [s for s in slots if s.disponible]

        return SlotsListResponse(
            profesional_id=profesional_id,
            slot_duracion_min=profesional.slot_duracion_min,
            desde=desde,
            hasta=hasta,
            slots=slots,
            total=len(disponibles)
        )

    async def get_slots_count(
        self,
        profesional_id: int,
        desde: date,
        hasta: date,
    ) -> int:
        """Get count of available slots (for metadata)."""
        return await self.slot_repo.get_slots_count(profesional_id, desde, hasta)
