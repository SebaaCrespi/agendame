"""Disponibilidad Service - Business logic for Disponibilidad and Excepciones."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.disponibilidad_repo import DisponibilidadRepo
from app.repositories.excepcion_repo import ExcepcionRepo
from app.schemas.profesional import (
    DisponibilidadCreate,
    DisponibilidadResponse,
    ExcepcionCreate,
    ExcepcionResponse,
    GrillaDisponibilidadResponse,
)


class DisponibilidadService:
    """Service layer for Disponibilidad and ExcepcionDisponibilidad business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.disp_repo = DisponibilidadRepo(session)
        self.exc_repo = ExcepcionRepo(session)

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
