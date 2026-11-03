"""Admin API endpoints for Turno management."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.turno import TurnoListResponse, TurnoResponse
from app.services.turno_service import TurnoService

router = APIRouter(prefix="/admin/turnos", tags=["Admin - Turnos"])


@router.get(
    "",
    response_model=TurnoListResponse,
    summary="Listar todos los turnos (Admin)",
    description="Lista paginada de todos los turnos con filtros opcionales: estado, fecha, profesional, cliente.",
)
async def listar_turnos_admin(
    estado: str | None = Query(None, description="Filtrar por estado"),
    desde: date | None = Query(None, description="Fecha desde (inclusive)"),
    hasta: date | None = Query(None, description="Fecha hasta (inclusive)"),
    profesional_id: int | None = Query(None, ge=1, description="Filtrar por profesional"),
    cliente_id: int | None = Query(None, ge=1, description="Filtrar por cliente"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TurnoListResponse:
    """Listar todos los turnos con paginación y filtros (Admin)."""
    service = TurnoService(session)
    turnos, total = await service.get_all_turnos_admin(
        page=page,
        size=size,
        estado=estado,
        desde=desde,
        hasta=hasta,
        profesional_id=profesional_id,
        cliente_id=cliente_id,
    )

    pages = (total + size - 1) // size if size > 0 else 0

    return TurnoListResponse(
        items=turnos,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/{turno_id}",
    response_model=TurnoResponse,
    summary="Obtener turno por ID (Admin)",
    description="Obtiene detalle completo de cualquier turno sin restricción de ownership.",
)
async def obtener_turno_admin(
    turno_id: int = Path(..., ge=1, description="ID del turno"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TurnoResponse:
    """Obtener turno por ID (Admin)."""
    service = TurnoService(session)
    turno = await service.get_turno_by_id_admin(turno_id)

    if not turno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")

    return turno
