"""Profesional Service - Business logic for Profesional."""


from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profesional import Profesional
from app.models.user import UserRole
from app.repositories.profesional_repo import ProfesionalRepo
from app.repositories.user_repo import UserRepo
from app.schemas.pagination import FilterParams, PageParams
from app.schemas.profesional import (
    DisponibilidadResponse,
    ExcepcionResponse,
    GrillaDisponibilidadResponse,
    MiPerfilResponse,
    ProfesionalCreate,
    ProfesionalListResponse,
    ProfesionalResponse,
    ProfesionalUpdate,
    ServicioResponse,
)


class ProfesionalService:
    """Service layer for Profesional business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ProfesionalRepo(session)
        self.user_repo = UserRepo(session)

    # =========================================================================
    # Admin methods
    # =========================================================================

    async def crear_profesional_admin(self, data: ProfesionalCreate) -> Profesional:
        """Create profesional with associated user (Admin only)."""
        # Check if email already exists in users
        existing_user = await self.user_repo.get_by_email(data.email)
        if existing_user:
            raise ValueError("Email ya registrado en el sistema")

        # Create user with PROVEEDOR role
        user = await self.user_repo.create(
            email=data.email,
            password=data.password,
            nombre=f"{data.nombre} {data.apellido}",
            rol=UserRole.PROVEEDOR,
        )

        # Create profesional linked to user
        profesional = await self.repo.create(data, user)
        await self.session.commit()
        await self.session.refresh(profesional)
        return profesional

    async def obtener_profesional(self, profesional_id: int) -> Profesional | None:
        """Get profesional by ID with relations."""
        return await self.repo.get_by_id_with_relations(profesional_id)

    async def listar_profesionales_admin(
        self,
        params: PageParams,
        filters: FilterParams,
    ) -> ProfesionalListResponse:
        """List profesionales with pagination (Admin)."""
        items, total = await self.repo.list_paginated(params, filters)

        pages = (total + params.size - 1) // params.size if params.size > 0 else 0

        return ProfesionalListResponse(
            items=[ProfesionalResponse.model_validate(p) for p in items],
            total=total,
            page=params.page,
            size=params.size,
            pages=pages
        )

    async def _validar_baja(self, profesional_id: int) -> bool:
        """
        Regla de baja (CU-10): no se desactiva un profesional con turnos activos sin terminar.

        Devuelve False si el profesional no existe; ValueError si tiene turnos pendientes.
        """
        result = await self.repo.get_with_turnos_count(profesional_id)
        if not result:
            return False
        turnos_futuros = result["turnos_futuros"]
        if isinstance(turnos_futuros, int) and turnos_futuros > 0:
            plural = "turno pendiente" if turnos_futuros == 1 else "turnos pendientes"
            raise ValueError(
                f"No se puede desactivar: tiene {turnos_futuros} {plural}. Reasignalos o cancelalos primero."
            )
        return True

    async def listar_activos(self, q: str | None = None, limite: int = 50) -> list[Profesional]:
        """Profesionales activos, opcionalmente filtrados por nombre (listado público y chatbot)."""
        items, _ = await self.repo.list_paginated(PageParams(page=1, size=limite), FilterParams(q=q, activo=True))
        return list(items)

    async def actualizar_profesional(
        self, profesional_id: int, data: ProfesionalUpdate
    ) -> Profesional | None:
        """Update profesional (Admin). Desactivar por acá aplica la misma regla que el DELETE."""
        if data.activo is False:
            actual = await self.repo.get_by_id(profesional_id)
            if actual and actual.activo and not await self._validar_baja(profesional_id):
                return None
        profesional = await self.repo.update(profesional_id, data)
        if profesional:
            await self.session.commit()
            await self.session.refresh(profesional)
        return profesional

    async def desactivar_profesional(self, profesional_id: int) -> bool:
        """Soft delete profesional with validation of future turnos (Admin)."""
        if not await self._validar_baja(profesional_id):
            return False

        success = await self.repo.soft_delete(profesional_id)
        if success:
            await self.session.commit()
        return success

    # =========================================================================
    # Profesional (own) methods
    # =========================================================================

    async def obtener_mi_perfil(self, user_id: int) -> MiPerfilResponse | None:
        """Get complete profile for authenticated profesional."""
        profesional = await self.repo.get_by_user_id(user_id)
        if not profesional:
            return None

        # Load relations
        profesional = await self.repo.get_by_id_with_relations(profesional.id)
        if not profesional:
            return None

        # Build response
        from app.repositories.disponibilidad_repo import DisponibilidadRepo
        from app.repositories.excepcion_repo import ExcepcionRepo
        from app.repositories.servicio_repo import ServicioRepo

        servicio_repo = ServicioRepo(self.session)
        disponibilidad_repo = DisponibilidadRepo(self.session)
        excepcion_repo = ExcepcionRepo(self.session)

        servicios = await servicio_repo.get_activos_by_profesional(profesional.id)
        disponibilidades = await disponibilidad_repo.get_activa_by_profesional(profesional.id)
        excepciones = await excepcion_repo.get_by_profesional(profesional.id)

        # Build grilla response
        grilla = GrillaDisponibilidadResponse(
            profesional_id=profesional.id,
            slot_duracion_min=profesional.slot_duracion_min,
            grilla=[DisponibilidadResponse.model_validate(d) for d in disponibilidades]
        )

        return MiPerfilResponse(
            profesional=ProfesionalResponse.model_validate(profesional),
            servicios=[ServicioResponse.model_validate(s) for s in servicios],
            disponibilidad=grilla,
            excepciones=[ExcepcionResponse.model_validate(e) for e in excepciones]
        )

    async def obtener_por_usuario(self, user_id: int) -> Profesional | None:
        """Get profesional by user ID."""
        return await self.repo.get_by_user_id(user_id)

    async def actualizar_mi_perfil(self, user_id: int, data: ProfesionalUpdate) -> Profesional | None:
        """Update own perfil (Profesional)."""
        profesional = await self.repo.get_by_user_id(user_id)
        if not profesional:
            return None

        # Don't allow changing activo status via this endpoint
        update_data = data.model_dump(exclude_unset=True)
        update_data.pop("activo", None)

        from app.schemas.profesional import ProfesionalUpdate
        filtered_update = ProfesionalUpdate(**update_data)

        updated = await self.repo.update(profesional.id, filtered_update)
        if updated:
            await self.session.commit()
            await self.session.refresh(updated)
        return updated
