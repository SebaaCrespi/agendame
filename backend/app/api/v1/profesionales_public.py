"""Public API endpoints for Profesional browsing.

Sin login: un visitante elige profesional, servicio y horario antes de crear su cuenta.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.core.database import get_db
from app.models.user import User
from app.schemas.pagination import FilterParams, PageParams
from app.schemas.profesional import (
    ExcepcionResponse,
    GrillaDisponibilidadResponse,
    ProfesionalPublicListResponse,
    ProfesionalPublicResponse,
    ServicioResponse,
    SlotsListResponse,
)
from app.services.disponibilidad_service import DisponibilidadService
from app.services.profesional_service import ProfesionalService
from app.services.servicio_service import ServicioService
from app.services.slot_service import SlotService

router = APIRouter(prefix="/profesionales", tags=["Público - Profesionales"])


@router.get(
    "",
    response_model=ProfesionalPublicListResponse,
    summary="Listar profesionales (Público)",
    description="Lista paginada de profesionales activos con filtros. Acceso público/CLIENTE."
)
async def listar_profesionales_publico(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página (máx 50 para público)"),
    q: str | None = Query(None, description="Búsqueda por nombre"),
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ProfesionalPublicListResponse:
    """Listar profesionales públicos con paginación y filtros."""
    # Limit public page size to 50
    size = min(size, 50)

    params = PageParams(page=page, size=size)
    filters = FilterParams(q=q, activo=True)  # Solo activos para público

    service = ProfesionalService(session)
    # Use the admin list method but with public filters
    items, total = await service.repo.list_paginated(params, filters)

    pages = (total + params.size - 1) // params.size if params.size > 0 else 0

    return ProfesionalPublicListResponse(
        items=[ProfesionalPublicResponse.from_model(p) for p in items],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages
    )


@router.get(
    "/{profesional_id}",
    response_model=ProfesionalPublicResponse,
    summary="Obtener profesional por ID (Público)",
    description="Obtiene perfil público de un profesional (solo si está activo)."
)
async def obtener_profesional_publico(
    profesional_id: int = Path(..., ge=1, description="ID del profesional"),
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ProfesionalPublicResponse:
    """Obtener profesional público por ID."""
    service = ProfesionalService(session)
    profesional = await service.obtener_profesional(profesional_id)

    if not profesional or not profesional.activo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesional no encontrado")

    return ProfesionalPublicResponse.from_model(profesional)


@router.get(
    "/{profesional_id}/servicios",
    response_model=list[ServicioResponse],
    summary="Listar servicios de un profesional (Público)",
    description="Lista servicios activos de un profesional específico."
)
async def listar_servicios_publico(
    profesional_id: int = Path(..., ge=1, description="ID del profesional"),
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[ServicioResponse]:
    """Listar servicios públicos de un profesional."""
    # Verify profesional exists and is active
    prof_service = ProfesionalService(session)
    profesional = await prof_service.obtener_profesional(profesional_id)
    if not profesional or not profesional.activo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesional no encontrado")

    service = ServicioService(session)
    servicios = await service.obtener_para_slots(profesional_id)
    return [ServicioResponse.model_validate(s) for s in servicios]


@router.get(
    "/{profesional_id}/disponibilidad",
    response_model=GrillaDisponibilidadResponse,
    summary="Obtener grilla de disponibilidad (Público)",
    description="Retorna la grilla semanal de disponibilidad de un profesional."
)
async def obtener_grilla_publico(
    profesional_id: int = Path(..., ge=1, description="ID del profesional"),
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> GrillaDisponibilidadResponse:
    """Obtener grilla de disponibilidad pública."""
    # Verify profesional exists and is active
    prof_service = ProfesionalService(session)
    profesional = await prof_service.obtener_profesional(profesional_id)
    if not profesional or not profesional.activo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesional no encontrado")

    service = DisponibilidadService(session)
    return await service.obtener_mi_grilla(profesional_id)


@router.get(
    "/{profesional_id}/excepciones",
    response_model=list[ExcepcionResponse],
    summary="Listar excepciones de disponibilidad (Público)",
    description="Lista excepciones de disponibilidad de un profesional en rango de fechas."
)
async def listar_excepciones_publico(
    profesional_id: int = Path(..., ge=1, description="ID del profesional"),
    desde: date | None = Query(None, description="Fecha desde (inclusive)"),
    hasta: date | None = Query(None, description="Fecha hasta (inclusive)"),
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> list[ExcepcionResponse]:
    """Listar excepciones públicas de un profesional."""
    # Verify profesional exists and is active
    prof_service = ProfesionalService(session)
    profesional = await prof_service.obtener_profesional(profesional_id)
    if not profesional or not profesional.activo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesional no encontrado")

    service = DisponibilidadService(session)
    return await service.obtener_excepciones(profesional_id, desde, hasta)


@router.get(
    "/{profesional_id}/slots",
    response_model=SlotsListResponse,
    summary="Obtener slots disponibles (Público)",
    description="Genera slots disponibles para un profesional en rango de fechas. "
                "Máximo 60 días. Rate limiting estricto aplicado."
)
async def obtener_slots_publico(
    profesional_id: int = Path(..., ge=1, description="ID del profesional"),
    desde: date = Query(..., description="Fecha desde (inclusive)"),
    hasta: date = Query(..., description="Fecha hasta (inclusive)"),
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> SlotsListResponse:
    """Obtener slots disponibles públicos."""
    # Verify profesional exists and is active
    prof_service = ProfesionalService(session)
    profesional = await prof_service.obtener_profesional(profesional_id)
    if not profesional or not profesional.activo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesional no encontrado")

    service = SlotService(session)
    try:
        return await service.generar_slots_disponibles(profesional_id, desde, hasta)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
