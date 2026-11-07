"""Servicio Service - Business logic for Servicio."""


from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profesional import Servicio
from app.repositories.servicio_repo import ServicioRepo
from app.schemas.profesional import ServicioCreate, ServicioUpdate


class ServicioService:
    """Service layer for Servicio business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ServicioRepo(session)

    async def crear_servicio(
        self, profesional_id: int, data: ServicioCreate
    ) -> Servicio:
        """Create servicio for a profesional."""
        # Validate unique nombre for this profesional
        exists = await self.repo.exists_nombre_for_profesional(profesional_id, data.nombre)
        if exists:
            raise ValueError("Nombre de servicio ya existe para este profesional")

        servicio = await self.repo.create(profesional_id, data)
        await self.session.commit()
        await self.session.refresh(servicio)
        return servicio

    async def obtener_servicio(self, servicio_id: int) -> Servicio | None:
        """Get servicio by ID."""
        return await self.repo.get_by_id(servicio_id)

    async def listar_mis_servicios(self, profesional_id: int) -> list[Servicio]:
        """List all active servicios for a profesional."""
        return await self.repo.get_activos_by_profesional(profesional_id)

    async def actualizar_servicio(
        self, servicio_id: int, profesional_id: int, data: ServicioUpdate
    ) -> Servicio | None:
        """Update servicio (ownership validated)."""
        # Verify ownership
        servicio = await self.repo.get_by_id_and_profesional(servicio_id, profesional_id)
        if not servicio:
            return None

        # Validate unique nombre if changing
        if data.nombre is not None and data.nombre != servicio.nombre:
            exists = await self.repo.exists_nombre_for_profesional(
                profesional_id, data.nombre, exclude_id=servicio_id
            )
            if exists:
                raise ValueError("Nombre de servicio ya existe para este profesional")

        updated = await self.repo.update(servicio_id, data)
        if updated:
            await self.session.commit()
            await self.session.refresh(updated)
        return updated

    async def desactivar_servicio(self, servicio_id: int, profesional_id: int) -> bool:
        """Soft delete servicio (ownership validated)."""
        servicio = await self.repo.get_by_id_and_profesional(servicio_id, profesional_id)
        if not servicio:
            return False

        success = await self.repo.soft_delete(servicio_id)
        if success:
            await self.session.commit()
        return success

    async def obtener_para_slots(self, profesional_id: int) -> list[Servicio]:
        """Get active servicios for slot generation (ordered by duration)."""
        return await self.repo.get_activos_by_profesional(profesional_id)
