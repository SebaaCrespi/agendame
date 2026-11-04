"""Cliente API endpoints for Turnos."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_cliente
from app.core.database import get_db
from app.models.turno import TurnoEstado
from app.models.user import User
from app.schemas.turno import (
    DisponibilidadResponse,
    MomentoTurno,
    TurnoCancelar,
    TurnoCreate,
    TurnoFiltros,
    TurnoListResponse,
    TurnoResponse,
)
from app.services.turno_service import TurnoService

router = APIRouter(prefix="/turnos", tags=["Cliente - Turnos"])


@router.get(
    "/disponibilidad",
    response_model=DisponibilidadResponse,
    summary="Consultar disponibilidad de profesionales",
    description="Retorna slots disponibles agrupados por profesional y fecha. "
                "Filtros opcionales: profesional_id, servicio_id. "
                "Rango máximo: 60 días.",
)
async def consultar_disponibilidad(
    desde: date = Query(..., description="Fecha desde (inclusive)"),
    hasta: date = Query(..., description="Fecha hasta (inclusive)"),
    profesional_id: int | None = Query(None, ge=1, description="Filtrar por profesional"),
    servicio_id: int | None = Query(None, ge=1, description="Filtrar por servicio"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
) -> DisponibilidadResponse:
    """Consultar disponibilidad de profesionales en rango de fechas."""
    service = TurnoService(session)
    try:
        return await service.consultar_disponibilidad(
            profesional_id=profesional_id,
            servicio_id=servicio_id,
            desde=desde,
            hasta=hasta,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None


@router.post(
    "",
    response_model=TurnoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reserva manual",
    description="Crea una nueva reserva para el cliente autenticado. "
                "Valida: profesional activo, servicio del profesional, slot libre. "
                "El turno se crea en estado CONFIRMADO automáticamente.",
)
async def crear_reserva(
    data: TurnoCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
) -> TurnoResponse:
    """Crear reserva manual de turno."""
    cliente = await TurnoService(session)._get_cliente_by_user_id(current_user.id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado. Complete su perfil primero."
        )

    service = TurnoService(session)
    try:
        return await service.crear_reserva_manual(
            cliente_id=cliente.id,
            profesional_id=data.profesional_id,
            servicio_id=data.servicio_id,
            fecha=data.fecha,
            hora_inicio=data.hora_inicio,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None


@router.get(
    "/mis-turnos",
    response_model=TurnoListResponse,
    summary="Listar mis turnos",
    description="Lista paginada de turnos del cliente autenticado con filtros opcionales.",
)
async def listar_mis_turnos(
    estado: list[TurnoEstado] | None = Query(None, description="Filtrar por estado (se puede repetir)"),
    momento: MomentoTurno | None = Query(None, description="proximos | pasados"),
    desde: date | None = Query(None, description="Fecha desde (inclusive)"),
    hasta: date | None = Query(None, description="Fecha hasta (inclusive)"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
) -> TurnoListResponse:
    """Listar turnos del cliente autenticado."""
    cliente = await TurnoService(session)._get_cliente_by_user_id(current_user.id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    filtros = TurnoFiltros(estado=estado, momento=momento, desde=desde, hasta=hasta, page=page, size=size)
    service = TurnoService(session)
    turnos, total = await service.get_turnos_by_cliente(cliente.id, filtros)

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
    summary="Obtener detalle de mi turno",
    description="Obtiene el detalle de un turno específico del cliente autenticado.",
)
async def obtener_turno(
    turno_id: int = Path(..., ge=1, description="ID del turno"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
) -> TurnoResponse:
    """Obtener detalle de turno del cliente."""
    cliente = await TurnoService(session)._get_cliente_by_user_id(current_user.id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    service = TurnoService(session)
    turno = await service.get_turno_by_id(turno_id)

    if not turno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")

    # Verificar ownership
    if turno.cliente_id != cliente.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turno no encontrado"
        )

    return turno


@router.put(
    "/{turno_id}/cancelar",
    response_model=TurnoResponse,
    summary="Cancelar mi turno",
    description="Cancela un turno del cliente autenticado. "
                "Solo turnos futuros (>2h antelación) en estado PENDIENTE o CONFIRMADO. "
                "El estado cambia a CANCELADO_CLIENTE y el slot queda libre.",
)
async def cancelar_turno(
    data: TurnoCancelar,
    turno_id: int = Path(..., ge=1, description="ID del turno"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
) -> TurnoResponse:
    """Cancelar turno del cliente."""
    cliente = await TurnoService(session)._get_cliente_by_user_id(current_user.id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    service = TurnoService(session)
    try:
        return await service.cancelar_turno_cliente(
            turno_id=turno_id,
            cliente_id=cliente.id,
            motivo=data.motivo,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
