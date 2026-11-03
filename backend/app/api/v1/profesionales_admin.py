"""Admin API endpoints for Profesional management."""


from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.pagination import FilterParams, PageParams
from app.schemas.profesional import (
    ProfesionalCreate,
    ProfesionalListResponse,
    ProfesionalResponse,
    ProfesionalUpdate,
)
from app.services.profesional_service import ProfesionalService

router = APIRouter(prefix="/admin/profesionales", tags=["Admin - Profesionales"])


@router.post(
    "",
    response_model=ProfesionalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear profesional (Admin)",
    description="Crea un nuevo profesional y su usuario asociado con rol PROVEEDOR."
)
async def crear_profesional(
    data: ProfesionalCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ProfesionalResponse:
    """Crear profesional (Admin)."""
    service = ProfesionalService(session)
    try:
        profesional = await service.crear_profesional_admin(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from None
    return ProfesionalResponse.model_validate(profesional)


@router.get(
    "",
    response_model=ProfesionalListResponse,
    summary="Listar profesionales (Admin)",
    description="Lista paginada de profesionales con filtros opcionales."
)
async def listar_profesionales(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    q: str | None = Query(None, description="Búsqueda por nombre"),
    activo: bool | None = Query(None, description="Filtrar por estado activo"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ProfesionalListResponse:
    """Listar profesionales con paginación y filtros (Admin)."""
    params = PageParams(page=page, size=size)
    filters = FilterParams(q=q, activo=activo)

    service = ProfesionalService(session)
    return await service.listar_profesionales_admin(params, filters)


@router.get(
    "/{profesional_id}",
    response_model=ProfesionalResponse,
    summary="Obtener profesional por ID (Admin)",
    description="Obtiene detalle completo de un profesional."
)
async def obtener_profesional(
    profesional_id: int = Path(..., ge=1, description="ID del profesional"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ProfesionalResponse:
    """Obtener profesional por ID (Admin)."""
    service = ProfesionalService(session)
    profesional = await service.obtener_profesional(profesional_id)
    if not profesional:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesional no encontrado")
    return ProfesionalResponse.model_validate(profesional)


@router.put(
    "/{profesional_id}",
    response_model=ProfesionalResponse,
    summary="Actualizar profesional (Admin)",
    description="Actualiza campos de un profesional."
)
async def actualizar_profesional(
    data: ProfesionalUpdate,
    profesional_id: int = Path(..., ge=1, description="ID del profesional"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ProfesionalResponse:
    """Actualizar profesional (Admin)."""
    service = ProfesionalService(session)
    profesional = await service.actualizar_profesional(profesional_id, data)
    if not profesional:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesional no encontrado")
    return ProfesionalResponse.model_validate(profesional)


@router.delete(
    "/{profesional_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar profesional (Admin)",
    description="Desactiva un profesional (soft delete). Bloqueado si tiene turnos futuros."
)
async def desactivar_profesional(
    profesional_id: int = Path(..., ge=1, description="ID del profesional"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Desactivar profesional (Admin)."""
    service = ProfesionalService(session)
    try:
        success = await service.desactivar_profesional(profesional_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from None

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesional no encontrado")
