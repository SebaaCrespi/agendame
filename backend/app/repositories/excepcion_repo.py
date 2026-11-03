"""ExcepcionDisponibilidad Repository - Data access layer for ExcepcionDisponibilidad model."""

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profesional import ExcepcionDisponibilidad, TipoExcepcion
from app.schemas.profesional import ExcepcionCreate, ExcepcionUpdate


class ExcepcionRepo:
    """Repository for ExcepcionDisponibilidad data access."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, profesional_id: int, exc_data: ExcepcionCreate) -> ExcepcionDisponibilidad:
        """Create a new excepcion for a profesional."""
        excepcion = ExcepcionDisponibilidad(
            profesional_id=profesional_id,
            fecha=exc_data.fecha,
            tipo=TipoExcepcion(exc_data.tipo),
            hora_inicio=exc_data.hora_inicio,
            hora_fin=exc_data.hora_fin,
            motivo=exc_data.motivo,
        )
        self.session.add(excepcion)
        await self.session.flush()
        await self.session.refresh(excepcion)
        return excepcion

    async def get_by_id(self, excepcion_id: int) -> ExcepcionDisponibilidad | None:
        """Get excepcion by ID."""
        stmt = select(ExcepcionDisponibilidad).where(ExcepcionDisponibilidad.id == excepcion_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_profesional(self, profesional_id: int) -> list[ExcepcionDisponibilidad]:
        """Get all excepciones for a profesional (ordered by fecha)."""
        stmt = select(ExcepcionDisponibilidad).where(
            ExcepcionDisponibilidad.profesional_id == profesional_id
        ).order_by(ExcepcionDisponibilidad.fecha)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_profesional_and_fecha(
        self, profesional_id: int, fecha: date
    ) -> ExcepcionDisponibilidad | None:
        """Get excepcion by profesional and fecha (unique constraint)."""
        stmt = select(ExcepcionDisponibilidad).where(
            ExcepcionDisponibilidad.profesional_id == profesional_id,
            ExcepcionDisponibilidad.fecha == fecha
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_profesional(
        self,
        profesional_id: int,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> list[ExcepcionDisponibilidad]:
        """List excepciones for a profesional with optional date range."""
        stmt = select(ExcepcionDisponibilidad).where(
            ExcepcionDisponibilidad.profesional_id == profesional_id
        )

        if desde:
            stmt = stmt.where(ExcepcionDisponibilidad.fecha >= desde)
        if hasta:
            stmt = stmt.where(ExcepcionDisponibilidad.fecha <= hasta)

        stmt = stmt.order_by(ExcepcionDisponibilidad.fecha)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_slot_generation(
        self, profesional_id: int, desde: date, hasta: date
    ) -> list[ExcepcionDisponibilidad]:
        """Get excepciones for slot generation in date range."""
        return await self.list_by_profesional(profesional_id, desde, hasta)

    async def update(self, excepcion_id: int, data: ExcepcionUpdate) -> ExcepcionDisponibilidad | None:
        """Update excepcion (only motivo can be updated)."""
        excepcion = await self.get_by_id(excepcion_id)
        if not excepcion:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(excepcion, field, value)

        await self.session.flush()
        await self.session.refresh(excepcion)
        return excepcion

    async def delete(self, excepcion_id: int) -> bool:
        """Delete excepcion by ID."""
        excepcion = await self.get_by_id(excepcion_id)
        if not excepcion:
            return False

        await self.session.delete(excepcion)
        await self.session.flush()
        return True

    async def delete_by_profesional(self, profesional_id: int) -> int:
        """Delete all excepciones for a profesional."""
        stmt = delete(ExcepcionDisponibilidad).where(
            ExcepcionDisponibilidad.profesional_id == profesional_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount
