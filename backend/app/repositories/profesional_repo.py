"""Profesional Repository - Data access layer for Profesional model."""

from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profesional import Profesional
from app.models.user import User
from app.schemas.pagination import FilterParams, PageParams
from app.schemas.profesional import ProfesionalCreate, ProfesionalUpdate


class ProfesionalRepo:
    """Repository for Profesional data access."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, profesional_data: ProfesionalCreate, user: User) -> Profesional:
        """Create a new profesional linked to a user."""
        profesional = Profesional(
            user_id=user.id,
            nombre=profesional_data.nombre,
            apellido=profesional_data.apellido,
            telefono=profesional_data.telefono,
            bio=profesional_data.bio,
            foto_url=profesional_data.foto_url,
            slot_duracion_min=profesional_data.slot_duracion_min,
            activo=True,
        )
        self.session.add(profesional)
        await self.session.flush()
        await self.session.refresh(profesional)
        return profesional

    async def get_by_id(self, profesional_id: int) -> Profesional | None:
        """Get profesional by ID."""
        stmt = select(Profesional).where(Profesional.id == profesional_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_relations(self, profesional_id: int) -> Profesional | None:
        """Get profesional by ID with all relations loaded."""
        stmt = (
            select(Profesional)
            .where(Profesional.id == profesional_id)
            .options(
                selectinload(Profesional.user),
                selectinload(Profesional.servicios),
                selectinload(Profesional.disponibilidades),
                selectinload(Profesional.excepciones),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> Profesional | None:
        """Get profesional by user ID."""
        stmt = select(Profesional).where(Profesional.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Profesional | None:
        """Get profesional by user email (join with users table)."""
        stmt = (
            select(Profesional)
            .join(User, Profesional.user_id == User.id)
            .where(User.email == email)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        params: PageParams,
        filters: FilterParams,
    ) -> tuple[list[Profesional], int]:
        """List profesionales with pagination and filters."""
        stmt = select(Profesional).options(selectinload(Profesional.user))
        count_stmt = select(func.count(Profesional.id))

        # Apply filters
        if filters.activo is not None:
            stmt = stmt.where(Profesional.activo == filters.activo)
            count_stmt = count_stmt.where(Profesional.activo == filters.activo)

        if filters.q:
            search_term = f"%{filters.q}%"
            stmt = stmt.where(
                or_(
                    Profesional.nombre.ilike(search_term),
                    Profesional.apellido.ilike(search_term),
                )
            )
            count_stmt = count_stmt.where(
                or_(
                    Profesional.nombre.ilike(search_term),
                    Profesional.apellido.ilike(search_term),
                )
            )

        # Get total count
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination
        stmt = stmt.offset((params.page - 1) * params.size).limit(params.size)
        stmt = stmt.order_by(Profesional.nombre, Profesional.apellido)

        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def update(self, profesional_id: int, data: ProfesionalUpdate) -> Profesional | None:
        """Update profesional fields."""
        profesional = await self.get_by_id(profesional_id)
        if not profesional:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profesional, field, value)

        profesional.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(profesional)
        return profesional

    async def soft_delete(self, profesional_id: int) -> bool:
        """Soft delete profesional (set activo=False)."""
        profesional = await self.get_by_id(profesional_id)
        if not profesional:
            return False

        profesional.activo = False
        profesional.updated_at = datetime.now(UTC)
        await self.session.flush()
        return True

    async def exists_by_user_id(self, user_id: int) -> bool:
        """Check if profesional exists for user ID."""
        stmt = select(Profesional.id).where(Profesional.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count_active(self) -> int:
        """Count active profesionales."""
        stmt = select(func.count(Profesional.id)).where(Profesional.activo)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_with_turnos_count(self, profesional_id: int) -> dict[str, object] | None:
        """Get profesional with future turnos count (for soft delete validation)."""
        from app.models.turno import Turno, TurnoEstado

        profesional = await self.get_by_id(profesional_id)
        if not profesional:
            return None

        # Count future turnos (CONFIRMADO, PENDIENTE, EN_CURSO)
        stmt = select(func.count(Turno.id)).where(
            Turno.profesional_id == profesional_id,
            Turno.estado.in_([TurnoEstado.CONFIRMADO, TurnoEstado.PENDIENTE, TurnoEstado.EN_CURSO]),
            Turno.fecha_inicio >= func.date(func.now())
        )
        result = await self.session.execute(stmt)
        turnos_futuros = result.scalar_one()

        return {
            "profesional": profesional,
            "turnos_futuros": turnos_futuros
        }
