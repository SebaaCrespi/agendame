"""Profesional API endpoints for own profile management (PROVEEDOR role)."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_proveedor
from app.core.database import get_db
from app.models.profesional import Profesional
from app.models.turno import TurnoEstado
from app.models.user import User
from app.schemas.profesional import (
    DisponibilidadCreate,
    ExcepcionCreate,
    ExcepcionResponse,
    GrillaDisponibilidadResponse,
    MiPerfilResponse,
    ProfesionalResponse,
    ProfesionalUpdate,
    ServicioCreate,
    ServicioResponse,
    ServicioUpdate,
    SlotsListResponse,
)
from app.schemas.turno import (
    MomentoTurno,
    TurnoCancelar,
    TurnoEstadoUpdate,
    TurnoFiltros,
    TurnoListResponse,
    TurnoNotasUpdate,
    TurnoReasignar,
    TurnoResponse,
)
from app.services.disponibilidad_service import DisponibilidadService
from app.services.profesional_service import ProfesionalService
from app.services.servicio_service import ServicioService
from app.services.turno_service import TurnoService

router = APIRouter(prefix="/profesionales/me", tags=["Profesional - Mi Perfil"])


async def get_mi_profesional(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_proveedor),
) -> Profesional:
    """Perfil profesional del usuario autenticado (404 si no tiene)."""
    profesional = await ProfesionalService(session).obtener_por_usuario(current_user.id)
    if not profesional:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil profesional no encontrado")
    return profesional


# =============================================================================
# Perfil completo
# =============================================================================

@router.get(
    "",
    response_model=MiPerfilResponse,
    summary="Obtener mi perfil completo",
    description="Retorna perfil, servicios, grilla de disponibilidad y excepciones del profesional autenticado."
)
async def obtener_mi_perfil(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_proveedor),
) -> MiPerfilResponse:
    """Obtener mi perfil completo (Profesional)."""
    service = ProfesionalService(session)
    perfil = await service.obtener_mi_perfil(current_user.id)
    if not perfil:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil profesional no encontrado")
    return perfil


@router.put(
    "",
    response_model=ProfesionalResponse,
    summary="Actualizar mi perfil",
    description="Actualiza datos del perfil del profesional autenticado (no permite cambiar estado activo)."
)
async def actualizar_mi_perfil(
    data: ProfesionalUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_proveedor),
) -> ProfesionalResponse:
    """Actualizar mi perfil (Profesional)."""
    service = ProfesionalService(session)
    profesional = await service.actualizar_mi_perfil(current_user.id, data)
    if not profesional:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil profesional no encontrado")
    return ProfesionalResponse.model_validate(profesional)


# =============================================================================
# Servicios
# =============================================================================

@router.get(
    "/servicios",
    response_model=list[ServicioResponse],
    summary="Listar mis servicios",
    description="Lista todos los servicios activos del profesional autenticado."
)
async def listar_mis_servicios(
    session: AsyncSession = Depends(get_db),
    profesional: Profesional = Depends(get_mi_profesional),
) -> list[ServicioResponse]:
    """Listar mis servicios (Profesional)."""
    service = ServicioService(session)
    servicios = await service.listar_mis_servicios(profesional.id)
    return [ServicioResponse.model_validate(s) for s in servicios]


@router.post(
    "/servicios",
    response_model=ServicioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear servicio",
    description="Crea un nuevo servicio para el profesional autenticado."
)
async def crear_servicio(
    data: ServicioCreate,
    session: AsyncSession = Depends(get_db),
    profesional: Profesional = Depends(get_mi_profesional),
) -> ServicioResponse:
    """Crear servicio (Profesional)."""
    service = ServicioService(session)
    try:
        servicio = await service.crear_servicio(profesional.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from None
    return ServicioResponse.model_validate(servicio)


@router.put(
    "/servicios/{servicio_id}",
    response_model=ServicioResponse,
    summary="Actualizar servicio",
    description="Actualiza un servicio propio del profesional autenticado."
)
async def actualizar_servicio(
    data: ServicioUpdate,
    servicio_id: int = Path(..., ge=1, description="ID del servicio"),
    session: AsyncSession = Depends(get_db),
    profesional: Profesional = Depends(get_mi_profesional),
) -> ServicioResponse:
    """Actualizar servicio (Profesional)."""
    service = ServicioService(session)
    try:
        servicio = await service.actualizar_servicio(servicio_id, profesional.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from None

    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")
    return ServicioResponse.model_validate(servicio)


@router.delete(
    "/servicios/{servicio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar servicio",
    description="Desactiva (soft delete) un servicio propio del profesional autenticado."
)
async def desactivar_servicio(
    servicio_id: int = Path(..., ge=1, description="ID del servicio"),
    session: AsyncSession = Depends(get_db),
    profesional: Profesional = Depends(get_mi_profesional),
) -> None:
    """Desactivar servicio (Profesional)."""
    service = ServicioService(session)
    success = await service.desactivar_servicio(servicio_id, profesional.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")


# =============================================================================
# Disponibilidad (Grilla semanal)
# =============================================================================

@router.get(
    "/disponibilidad",
    response_model=GrillaDisponibilidadResponse,
    summary="Obtener mi grilla de disponibilidad",
    description="Retorna la grilla semanal completa del profesional autenticado."
)
async def obtener_mi_grilla(
    session: AsyncSession = Depends(get_db),
    profesional: Profesional = Depends(get_mi_profesional),
) -> GrillaDisponibilidadResponse:
    """Obtener mi grilla de disponibilidad (Profesional)."""
    service = DisponibilidadService(session)
    try:
        return await service.obtener_mi_grilla(profesional.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


@router.put(
    "/disponibilidad",
    response_model=GrillaDisponibilidadResponse,
    summary="Actualizar grilla completa",
    description="Reemplaza toda la grilla semanal (bulk replace). Máximo 1 entrada por día."
)
async def actualizar_grilla_completa(
    grilla: list[DisponibilidadCreate],
    session: AsyncSession = Depends(get_db),
    profesional: Profesional = Depends(get_mi_profesional),
) -> GrillaDisponibilidadResponse:
    """Actualizar grilla completa (Profesional)."""
    service = DisponibilidadService(session)
    try:
        return await service.actualizar_grilla_completa(profesional.id, grilla)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None


# =============================================================================
# Excepciones de disponibilidad
# =============================================================================

@router.get(
    "/excepciones",
    response_model=list[ExcepcionResponse],
    summary="Listar mis excepciones",
    description="Lista excepciones de disponibilidad con filtros opcionales de fecha."
)
async def obtener_excepciones(
    desde: date | None = Query(None, description="Fecha desde (inclusive)"),
    hasta: date | None = Query(None, description="Fecha hasta (inclusive)"),
    session: AsyncSession = Depends(get_db),
    profesional: Profesional = Depends(get_mi_profesional),
) -> list[ExcepcionResponse]:
    """Listar mis excepciones (Profesional)."""
    service = DisponibilidadService(session)
    return await service.obtener_excepciones(profesional.id, desde, hasta)


@router.post(
    "/excepciones",
    response_model=ExcepcionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear excepción",
    description="Crea una excepción de disponibilidad (día cerrado u horario especial)."
)
async def agregar_excepcion(
    data: ExcepcionCreate,
    session: AsyncSession = Depends(get_db),
    profesional: Profesional = Depends(get_mi_profesional),
) -> ExcepcionResponse:
    """Crear excepción (Profesional)."""
    service = DisponibilidadService(session)
    try:
        return await service.agregar_excepcion(profesional.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from None


@router.delete(
    "/excepciones/{excepcion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar excepción",
    description="Elimina una excepción de disponibilidad propia."
)
async def eliminar_excepcion(
    excepcion_id: int = Path(..., ge=1, description="ID de la excepción"),
    session: AsyncSession = Depends(get_db),
    profesional: Profesional = Depends(get_mi_profesional),
) -> None:
    """Eliminar excepción (Profesional)."""
    service = DisponibilidadService(session)
    success = await service.eliminar_excepcion(profesional.id, excepcion_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Excepción no encontrada")


@router.get(
    "/slots",
    response_model=SlotsListResponse,
    summary="Obtener mis slots",
    description="Slots propios en un rango (máximo 60 días), opcionalmente con la duración de un servicio "
                "propio y excluyendo un turno propio de los ocupados (para reasignarlo).",
)
async def obtener_mis_slots(
    desde: date = Query(..., description="Fecha desde (inclusive)"),
    hasta: date = Query(..., description="Fecha hasta (inclusive)"),
    servicio_id: int | None = Query(None, ge=1, description="Servicio propio cuya duración usar"),
    excluir_turno_id: int | None = Query(None, ge=1, description="Turno que no cuenta como ocupado"),
    session: AsyncSession = Depends(get_db),
    profesional: Profesional = Depends(get_mi_profesional),
) -> SlotsListResponse:
    """Slots del profesional autenticado (CU-08)."""
    try:
        return await TurnoService(session).obtener_slots_profesional(
            profesional.id, desde, hasta, servicio_id=servicio_id, excluir_turno_id=excluir_turno_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None


# =============================================================================
# Turnos (Gestión por Profesional)
# =============================================================================

@router.get(
    "/turnos",
    response_model=TurnoListResponse,
    summary="Listar mis turnos",
    description="Lista paginada de turnos del profesional autenticado con filtros opcionales.",
)
async def listar_mis_turnos(
    estado: list[TurnoEstado] | None = Query(None, description="Filtrar por estado (se puede repetir)"),
    momento: MomentoTurno | None = Query(None, description="proximos | pasados"),
    desde: date | None = Query(None, description="Fecha desde (inclusive)"),
    hasta: date | None = Query(None, description="Fecha hasta (inclusive)"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    servicio_id: int | None = Query(None, ge=1, description="Filtrar por servicio"),
    cliente: str | None = Query(None, min_length=1, max_length=100, description="Buscar por nombre de cliente"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_proveedor),
) -> TurnoListResponse:
    """Listar turnos del profesional autenticado."""
    # Obtener profesional_id del usuario actual
    prof_service = ProfesionalService(session)
    profesional = await prof_service.obtener_por_usuario(current_user.id)
    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil profesional no encontrado"
        )

    filtros = TurnoFiltros(
        estado=estado,
        momento=momento,
        desde=desde,
        hasta=hasta,
        page=page,
        size=size,
        servicio_id=servicio_id,
        cliente=cliente,
    )
    service = TurnoService(session)
    turnos, total = await service.get_turnos_by_profesional(profesional.id, filtros)

    pages = (total + size - 1) // size if size > 0 else 0

    return TurnoListResponse(
        items=turnos,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/turnos/{turno_id}",
    response_model=TurnoResponse,
    summary="Obtener detalle de mi turno",
    description="Obtiene el detalle de un turno específico del profesional autenticado.",
)
async def obtener_turno_profesional(
    turno_id: int = Path(..., ge=1, description="ID del turno"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_proveedor),
) -> TurnoResponse:
    """Obtener detalle de turno del profesional."""
    prof_service = ProfesionalService(session)
    profesional = await prof_service.obtener_por_usuario(current_user.id)
    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil profesional no encontrado"
        )

    service = TurnoService(session)
    turno = await service.get_turno_by_id(turno_id)

    if not turno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")

    # Verificar ownership
    if turno.profesional_id != profesional.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turno no encontrado"
        )

    return turno


@router.put(
    "/turnos/{turno_id}/estado",
    response_model=TurnoResponse,
    summary="Cambiar estado de turno",
    description="Cambia el estado de un turno (CONFIRMADO → EN_CURSO → FINALIZADO). "
                "Solo transiciones válidas permitidas.",
)
async def cambiar_estado_turno(
    data: TurnoEstadoUpdate,
    turno_id: int = Path(..., ge=1, description="ID del turno"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_proveedor),
) -> TurnoResponse:
    """Cambiar estado de turno (Profesional)."""
    prof_service = ProfesionalService(session)
    profesional = await prof_service.obtener_por_usuario(current_user.id)
    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil profesional no encontrado"
        )

    service = TurnoService(session)
    try:
        return await service.cambiar_estado(
            turno_id=turno_id,
            profesional_id=profesional.id,
            nuevo_estado=TurnoEstado(data.nuevo_estado),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None


@router.put(
    "/turnos/{turno_id}/reasignar",
    response_model=TurnoResponse,
    summary="Reasignar turno a otro slot",
    description="Mueve un turno a otro slot libre del mismo profesional. "
                "Requiere: turno en PENDIENTE o CONFIRMADO, mismo servicio (duración), nuevo slot libre.",
)
async def reasignar_turno(
    data: TurnoReasignar,
    turno_id: int = Path(..., ge=1, description="ID del turno"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_proveedor),
) -> TurnoResponse:
    """Reasignar turno (Profesional)."""
    prof_service = ProfesionalService(session)
    profesional = await prof_service.obtener_por_usuario(current_user.id)
    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil profesional no encontrado"
        )

    service = TurnoService(session)
    try:
        return await service.reasignar_turno(
            turno_id=turno_id,
            profesional_id=profesional.id,
            nueva_fecha=data.nueva_fecha,
            nueva_hora_inicio=data.nueva_hora_inicio,
            motivo=data.motivo,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None


@router.put(
    "/turnos/{turno_id}/cancelar",
    response_model=TurnoResponse,
    summary="Cancelar turno por profesional",
    description="Cancela un turno futuro del profesional. "
                "Requiere motivo. Estado cambia a CANCELADO_PROFESIONAL y slot queda libre.",
)
async def cancelar_turno_profesional(
    data: TurnoCancelar,
    turno_id: int = Path(..., ge=1, description="ID del turno"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_proveedor),
) -> TurnoResponse:
    """Cancelar turno por profesional."""
    prof_service = ProfesionalService(session)
    profesional = await prof_service.obtener_por_usuario(current_user.id)
    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil profesional no encontrado"
        )

    service = TurnoService(session)
    try:
        return await service.cancelar_turno_profesional(
            turno_id=turno_id,
            profesional_id=profesional.id,
            motivo=data.motivo,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None


@router.put(
    "/turnos/{turno_id}/notas",
    response_model=TurnoResponse,
    summary="Agregar/actualizar notas internas",
    description="Agrega o actualiza notas internas del profesional en un turno.",
)
async def agregar_notas_turno(
    data: TurnoNotasUpdate,
    turno_id: int = Path(..., ge=1, description="ID del turno"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_proveedor),
) -> TurnoResponse:
    """Agregar notas internas (Profesional)."""
    prof_service = ProfesionalService(session)
    profesional = await prof_service.obtener_por_usuario(current_user.id)
    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil profesional no encontrado"
        )

    service = TurnoService(session)
    try:
        return await service.agregar_notas_profesional(
            turno_id=turno_id,
            profesional_id=profesional.id,
            notas=data.notas_profesional,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
