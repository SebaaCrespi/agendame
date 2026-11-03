"""Disponibilidad Repository - Data access layer for Disponibilidad model."""


from datetime import UTC

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profesional import DiaSemana, Disponibilidad
from app.schemas.profesional import DisponibilidadCreate, DisponibilidadUpdate


class DisponibilidadRepo:
    """Repository for Disponibilidad data access."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, profesional_id: int, disp_data: DisponibilidadCreate) -> Disponibilidad:
        """Create a new disponibilidad for a profesional."""
        disponibilidad = Disponibilidad(
            profesional_id=profesional_id,
            dia_semana=DiaSemana(disp_data.dia_semana),
            hora_inicio=disp_data.hora_inicio,
            hora_fin=disp_data.hora_fin,
            activo=True,
        )
        self.session.add(disponibilidad)
        await self.session.flush()
        await self.session.refresh(disponibilidad)
        return disponibilidad

    async def get_by_id(self, disponibilidad_id: int) -> Disponibilidad | None:
        """Get disponibilidad by ID."""
        stmt = select(Disponibilidad).where(Disponibilidad.id == disponibilidad_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_profesional(self, profesional_id: int) -> list[Disponibilidad]:
        """Get all disponibilidades for a profesional (ordered by day)."""
        stmt = select(Disponibilidad).where(
            Disponibilidad.profesional_id == profesional_id
        ).order_by(Disponibilidad.dia_semana)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_activa_by_profesional(self, profesional_id: int) -> list[Disponibilidad]:
        """Get active disponibilidades for a profesional (for slot generation)."""
        stmt = select(Disponibilidad).where(
            Disponibilidad.profesional_id == profesional_id,
            Disponibilidad.activo
        ).order_by(Disponibilidad.dia_semana)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, disponibilidad_id: int, data: DisponibilidadUpdate) -> Disponibilidad | None:
        """Update disponibilidad fields."""
        disponibilidad = await self.get_by_id(disponibilidad_id)
        if not disponibilidad:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(disponibilidad, field, value)

        from datetime import datetime
        disponibilidad.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(disponibilidad)
        return disponibilidad

    async def delete_by_profesional(self, profesional_id: int) -> int:
        """Delete all disponibilidades for a profesional (bulk delete)."""
        stmt = delete(Disponibilidad).where(Disponibilidad.profesional_id == profesional_id)
        result = await self.session.execute(stmt)
        return result.rowcount

    async def replace_all_for_profesional(
        self,
        profesional_id: int,
        grilla: list[DisponibilidadCreate]
    ) -> list[Disponibilidad]:
        """Bulk replace all disponibilidades for a profesional (grilla semanal)."""
        # Delete existing
        await self.delete_by_profesional(profesional_id)

        # Create new ones
        nuevas = []
        for disp_data in grilla:
            disponibilidad = Disponibilidad(
                profesional_id=profesional_id,
                dia_semana=DiaSemana(disp_data.dia_semana),
                hora_inicio=disp_data.hora_inicio,
                hora_fin=disp_data.hora_fin,
                activo=True,
            )
            self.session.add(disponibilidad)
            nuevas.append(disponibilidad)

        await self.session.flush()
        for d in nuevas:
            await self.session.refresh(d)

        # Return ordered by day
        nuevas.sort(key=lambda x: x.dia_semana.value)
        return nuevas
