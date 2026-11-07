"""Servicio Repository - Data access layer for Servicio model."""

from datetime import UTC

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profesional import Servicio
from app.schemas.pagination import PageParams
from app.schemas.profesional import ServicioCreate, ServicioUpdate


class ServicioRepo:
    """Repository for Servicio data access."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, profesional_id: int, servicio_data: ServicioCreate) -> Servicio:
        """Create a new servicio for a profesional."""
        servicio = Servicio(
            profesional_id=profesional_id,
            nombre=servicio_data.nombre,
            descripcion=servicio_data.descripcion,
            duracion_min=servicio_data.duracion_min,
            precio=servicio_data.precio,
            orden=servicio_data.orden,
            activo=True,
        )
        self.session.add(servicio)
        await self.session.flush()
        await self.session.refresh(servicio)
        return servicio

    async def get_by_id(self, servicio_id: int) -> Servicio | None:
        """Get servicio by ID."""
        stmt = select(Servicio).where(Servicio.id == servicio_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_profesional(self, servicio_id: int, profesional_id: int) -> Servicio | None:
        """Get servicio by ID and profesional ID (ownership check)."""
        stmt = select(Servicio).where(
            Servicio.id == servicio_id,
            Servicio.profesional_id == profesional_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_profesional(self, profesional_id: int) -> list[Servicio]:
        """Get all servicios for a profesional (active only)."""
        stmt = select(Servicio).where(
            Servicio.profesional_id == profesional_id,
            Servicio.activo
        ).order_by(Servicio.orden, Servicio.nombre)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_profesional(
        self,
        profesional_id: int,
        params: PageParams,
        activo: bool | None = None,
    ) -> tuple[list[Servicio], int]:
        """List servicios for a profesional with pagination."""
        stmt = select(Servicio).where(Servicio.profesional_id == profesional_id)
        count_stmt = select(func.count(Servicio.id)).where(Servicio.profesional_id == profesional_id)

        if activo is not None:
            stmt = stmt.where(Servicio.activo == activo)
            count_stmt = count_stmt.where(Servicio.activo == activo)

        # Get total count
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination
        stmt = stmt.offset((params.page - 1) * params.size).limit(params.size)
        stmt = stmt.order_by(Servicio.orden, Servicio.nombre)

        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def update(self, servicio_id: int, data: ServicioUpdate) -> Servicio | None:
        """Update servicio fields."""
        servicio = await self.get_by_id(servicio_id)
        if not servicio:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(servicio, field, value)

        from datetime import datetime
        servicio.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(servicio)
        return servicio

    async def soft_delete(self, servicio_id: int) -> bool:
        """Soft delete servicio (set activo=False)."""
        servicio = await self.get_by_id(servicio_id)
        if not servicio:
            return False

        servicio.activo = False
        from datetime import datetime
        servicio.updated_at = datetime.now(UTC)
        await self.session.flush()
        return True

    async def exists_nombre_for_profesional(
        self,
        profesional_id: int,
        nombre: str,
        exclude_id: int | None = None
    ) -> bool:
        """Check if a servicio with the same nombre exists for the profesional (case-insensitive)."""
        stmt = select(Servicio.id).where(
            Servicio.profesional_id == profesional_id,
            Servicio.nombre.ilike(nombre)
        )
        if exclude_id:
            stmt = stmt.where(Servicio.id != exclude_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_activos_by_profesional(self, profesional_id: int) -> list[Servicio]:
        """Get all active servicios for a profesional (for slot generation)."""
        stmt = select(Servicio).where(
            Servicio.profesional_id == profesional_id,
            Servicio.activo
        ).order_by(Servicio.duracion_min)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
