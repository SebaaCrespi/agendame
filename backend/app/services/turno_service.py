"""Turno Service - Business logic for appointments."""

import asyncio
from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.timeutils import ahora_negocio
from app.models.cliente import Cliente
from app.models.turno import TurnoEstado
from app.repositories.profesional_repo import ProfesionalRepo
from app.repositories.servicio_repo import ServicioRepo
from app.repositories.turno_repo import TurnoRepo
from app.schemas.profesional import SlotsListResponse
from app.schemas.turno import (
    ChatbotReservarRequest,
    ChatbotReservarResponse,
    DisponibilidadResponse,
    ProfesionalConSlotsResponse,
    SlotDisponibleResponse,
    TurnoFiltros,
    TurnoResponse,
)
from app.services.slot_service import SlotService

if TYPE_CHECKING:
    pass


def _aware(dt: datetime) -> datetime:
    """SQLite devuelve datetimes naive: los normalizamos a UTC."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


# Un lock por profesional: evita que dos reservas simultáneas tomen el mismo slot
# (SQLite no soporta SELECT ... FOR UPDATE). Válido para un único proceso.
_reserva_locks: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)


class TurnoService:
    """Service layer for Turno business logic."""

    # Configuración
    CANCELACION_CLIENTE_HORAS_ANTES = 2

    # Matriz de transiciones válidas de estado
    TRANSICIONES_VALIDAS: dict[TurnoEstado, list[TurnoEstado]] = {
        TurnoEstado.PENDIENTE: [
            TurnoEstado.CONFIRMADO,
            TurnoEstado.CANCELADO_CLIENTE,
            TurnoEstado.CANCELADO_PROFESIONAL,
        ],
        TurnoEstado.CONFIRMADO: [
            TurnoEstado.EN_CURSO,
            TurnoEstado.CANCELADO_CLIENTE,
            TurnoEstado.CANCELADO_PROFESIONAL,
        ],
        TurnoEstado.EN_CURSO: [
            TurnoEstado.FINALIZADO,
            TurnoEstado.NO_ASISTIO,
            TurnoEstado.CANCELADO_PROFESIONAL,
        ],
        TurnoEstado.FINALIZADO: [],
        TurnoEstado.CANCELADO_CLIENTE: [],
        TurnoEstado.CANCELADO_PROFESIONAL: [],
        TurnoEstado.NO_ASISTIO: [],
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.turno_repo = TurnoRepo(session)
        self.slot_service = SlotService(session)
        self.prof_repo = ProfesionalRepo(session)
        self.servicio_repo = ServicioRepo(session)

    # =========================================================================
    # Helpers privados
    # =========================================================================

    async def _get_cliente_by_user_id(self, user_id: int) -> Cliente | None:
        """Get cliente by user ID."""
        stmt = select(Cliente).where(Cliente.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_cliente(self, cliente_id: int) -> Cliente | None:
        """Get cliente by its own ID (clientes.id)."""
        return await self.session.get(Cliente, cliente_id)

    async def _validate_slot_libre(
        self, profesional_id: int, fecha_inicio: datetime, fecha_fin: datetime
    ) -> bool:
        """Check if a slot is free for a profesional."""
        # Get turnos that overlap with the requested slot
        turnos_ocupados = await self.turno_repo.get_turnos_ocupados(
            profesional_id, fecha_inicio.date(), fecha_fin.date()
        )

        for turno in turnos_ocupados:
            # Check overlap: new_start < existing_end AND new_end > existing_start
            if fecha_inicio < _aware(turno.fecha_fin) and fecha_fin > _aware(turno.fecha_inicio):
                return False
        return True

    async def _validar_transicion(self, estado_actual: TurnoEstado, nuevo_estado: TurnoEstado) -> bool:
        """Validate if state transition is allowed."""
        return nuevo_estado in self.TRANSICIONES_VALIDAS.get(estado_actual, [])

    # =========================================================================
    # Métodos públicos
    # =========================================================================

    async def consultar_disponibilidad(
        self,
        profesional_id: int | None,
        servicio_id: int | None,
        desde: date,
        hasta: date,
    ) -> DisponibilidadResponse:
        """
        Consulta disponibilidad agrupada por profesional y fecha.

        Si se proporciona profesional_id, filtra por ese profesional.
        Si se proporciona servicio_id, filtra profesionales que ofrecen ese servicio.
        """

        if profesional_id:
            # Un solo profesional
            profesionales = [await self.prof_repo.get_by_id(profesional_id)]
            if not profesionales[0] or not profesionales[0].activo:
                return DisponibilidadResponse(desde=desde, hasta=hasta, profesionales=[])
        else:
            # Todos los profesionales activos
            # Usamos list_paginated con page grande para obtener todos
            from app.schemas.pagination import FilterParams, PageParams
            profesionales, _ = await self.prof_repo.list_paginated(  # type: ignore[assignment]
                PageParams(page=1, size=100),
                FilterParams(activo=True),
            )

        profesionales_con_slots = []

        for prof in profesionales:
            if not prof or not prof.activo:
                continue

            # Si hay servicio_id, verificar que el profesional lo ofrezca
            duracion_min: int | None = None
            if servicio_id:
                servicio = await self.servicio_repo.get_by_id_and_profesional(servicio_id, prof.id)
                if not servicio:
                    continue
                duracion_min = servicio.duracion_min

            # Generar slots usando SlotService (cada slot cubre la duración del servicio)
            try:
                slots_response: SlotsListResponse = await self.slot_service.generar_slots_disponibles(
                    prof.id, desde, hasta, duracion_min=duracion_min
                )
            except ValueError:
                continue  # Profesional sin disponibilidad en rango

            # Agrupar slots por fecha
            slots_por_fecha: dict[str, list[SlotDisponibleResponse]] = {}
            for slot in slots_response.slots:
                fecha_str = slot.fecha.isoformat()
                if fecha_str not in slots_por_fecha:
                    slots_por_fecha[fecha_str] = []
                slots_por_fecha[fecha_str].append(
                    SlotDisponibleResponse(
                        fecha=slot.fecha,
                        hora_inicio=slot.hora_inicio,
                        hora_fin=slot.hora_fin,
                        disponible=slot.disponible,
                    )
                )

            profesionales_con_slots.append(
                ProfesionalConSlotsResponse(
                    profesional_id=prof.id,
                    profesional_nombre=f"{prof.nombre} {prof.apellido}",
                    slot_duracion_min=prof.slot_duracion_min,
                    slots_por_fecha=slots_por_fecha,
                )
            )

        return DisponibilidadResponse(
            desde=desde,
            hasta=hasta,
            profesionales=profesionales_con_slots,
        )

    async def crear_reserva_manual(
        self,
        cliente_id: int,
        profesional_id: int,
        servicio_id: int,
        fecha: date,
        hora_inicio: time,
    ) -> TurnoResponse:
        """
        Crear reserva manual por cliente.

        Valida:
        - Cliente existe
        - Profesional activo
        - Servicio pertenece al profesional
        - Slot libre (con lock para concurrencia)
        """
        # Validar cliente (cliente_id = clientes.id)
        cliente = await self._get_cliente(cliente_id)
        if not cliente:
            raise NotFoundException("Cliente", cliente_id)

        # Validar profesional
        profesional = await self.prof_repo.get_by_id(profesional_id)
        if not profesional or not profesional.activo:
            raise NotFoundException("Profesional", "no encontrado o inactivo")

        # Validar servicio
        servicio = await self.servicio_repo.get_by_id_and_profesional(servicio_id, profesional_id)
        if not servicio:
            raise NotFoundException("Servicio", "no encontrado o no pertenece al profesional")

        # Calcular fecha/hora fin
        fecha_inicio = datetime.combine(fecha, hora_inicio).replace(tzinfo=UTC)
        fecha_fin = fecha_inicio + timedelta(minutes=servicio.duracion_min)
        if fecha_inicio <= ahora_negocio():
            raise ValidationException("No se puede reservar un turno en el pasado")

        # Verificar y crear bajo lock, y commitear antes de soltarlo para que
        # una reserva concurrente vea el turno ya guardado.
        async with _reserva_locks[profesional_id]:
            # Se valida contra los mismos slots que muestra la disponibilidad:
            # cubre grilla, excepciones, cierre, alineación y solapamientos.
            slots = await self.slot_service.generar_slots_disponibles(
                profesional_id, fecha, fecha, duracion_min=servicio.duracion_min
            )
            inicio = hora_inicio.replace(tzinfo=None)
            slot = next((s for s in slots.slots if s.hora_inicio == inicio), None)
            if slot is None:
                raise ValidationException(
                    "El horario elegido está fuera de la atención del profesional "
                    "o el servicio no entra antes del cierre"
                )
            if not slot.disponible:
                raise ConflictException("El slot seleccionado ya no está disponible")

            # Crear turno
            turno_data = {
                "profesional_id": profesional_id,
                "cliente_id": cliente.id,
                "servicio_id": servicio_id,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "estado": TurnoEstado.PENDIENTE,
                "notas_cliente": None,
                "notas_profesional": None,
                "creado_por": "cliente",
            }
            turno = await self.turno_repo.crear_turno(turno_data)

            # Confirmar automáticamente
            turno.estado = TurnoEstado.CONFIRMADO
            turno.confirmado_en = datetime.now(UTC)
            await self.session.commit()
            await self.session.refresh(turno)

        return TurnoResponse.model_validate(turno)

    async def cancelar_turno_cliente(
        self, turno_id: int, cliente_id: int, motivo: str
    ) -> TurnoResponse:
        """
        Cancelar turno por cliente.

        Valida:
        - Turno pertenece al cliente
        - Estado en {PENDIENTE, CONFIRMADO}
        - >2h de antelación
        """
        turno = await self.turno_repo.get_by_id(turno_id)
        if not turno:
            raise NotFoundException("Turno", turno_id)

        # Verificar ownership (cliente_id = clientes.id). 404 para no revelar turnos ajenos
        if turno.cliente_id != cliente_id:
            raise NotFoundException("Turno", turno_id)

        # Validar estado
        if turno.estado not in (TurnoEstado.PENDIENTE, TurnoEstado.CONFIRMADO):
            raise ValidationException("Solo se pueden cancelar turnos pendientes o confirmados")

        # Validar antelación (>2 horas)
        ahora = ahora_negocio()
        fecha_inicio = _aware(turno.fecha_inicio)

        horas_antes = (fecha_inicio - ahora).total_seconds() / 3600
        if horas_antes <= self.CANCELACION_CLIENTE_HORAS_ANTES:
            raise ValidationException(
                f"Solo se puede cancelar con más de {self.CANCELACION_CLIENTE_HORAS_ANTES} horas de antelación"
            )

        # Cancelar
        turno_cancelado = await self.turno_repo.cancelar(
            turno_id=turno_id,
            cancelado_por="cliente",
            motivo=motivo,
            timestamp=datetime.now(UTC),
        )

        return TurnoResponse.model_validate(turno_cancelado)

    async def cancelar_turno_profesional(
        self, turno_id: int, profesional_id: int, motivo: str
    ) -> TurnoResponse:
        """
        Cancelar turno por profesional.

        Valida:
        - Turno pertenece al profesional
        - Estado futuro (no FINALIZADO, no cancelado)
        """
        turno = await self.turno_repo.get_by_id(turno_id)
        if not turno:
            raise NotFoundException("Turno", turno_id)

        # Verificar ownership
        if turno.profesional_id != profesional_id:
            raise NotFoundException("Turno", turno_id)

        # Validar estado (solo turnos futuros)
        if turno.estado in (
            TurnoEstado.FINALIZADO,
            TurnoEstado.CANCELADO_CLIENTE,
            TurnoEstado.CANCELADO_PROFESIONAL,
            TurnoEstado.NO_ASISTIO,
        ):
            raise ValidationException("No se puede cancelar un turno ya finalizado o cancelado")

        # Cancelar
        turno_cancelado = await self.turno_repo.cancelar(
            turno_id=turno_id,
            cancelado_por="profesional",
            motivo=motivo,
            timestamp=datetime.now(UTC),
        )

        return TurnoResponse.model_validate(turno_cancelado)

    async def cambiar_estado(
        self, turno_id: int, profesional_id: int, nuevo_estado: TurnoEstado
    ) -> TurnoResponse:
        """
        Cambiar estado de turno (profesional).

        Valida:
        - Turno pertenece al profesional
        - Transición válida según matriz
        """
        turno = await self.turno_repo.get_by_id(turno_id)
        if not turno:
            raise NotFoundException("Turno", turno_id)

        # Verificar ownership
        if turno.profesional_id != profesional_id:
            raise NotFoundException("Turno", turno_id)

        # Validar transición
        if not await self._validar_transicion(turno.estado, nuevo_estado):
            raise ValidationException(
                f"Transición inválida: {turno.estado.value} → {nuevo_estado.value}"
            )

        # Determinar qué timestamp actualizar
        timestamp_campo = None
        if nuevo_estado == TurnoEstado.CONFIRMADO:
            timestamp_campo = "confirmado_en"
        elif nuevo_estado == TurnoEstado.FINALIZADO:
            timestamp_campo = "finalizado_en"

        # Actualizar
        turno_actualizado = await self.turno_repo.actualizar_estado(
            turno_id, nuevo_estado, timestamp_campo
        )

        return TurnoResponse.model_validate(turno_actualizado)

    async def reasignar_turno(
        self,
        turno_id: int,
        profesional_id: int,
        nueva_fecha: date,
        nueva_hora_inicio: time,
        motivo: str,
    ) -> TurnoResponse:
        """
        Reasignar turno a otro slot (profesional).

        Valida:
        - Turno pertenece al profesional
        - Estado en {PENDIENTE, CONFIRMADO}
        - Nuevo slot libre
        - Mismo servicio (misma duración)
        """
        turno = await self.turno_repo.get_by_id(turno_id)
        if not turno:
            raise NotFoundException("Turno", turno_id)

        # Verificar ownership
        if turno.profesional_id != profesional_id:
            raise NotFoundException("Turno", turno_id)

        # Validar estado
        if turno.estado not in (TurnoEstado.PENDIENTE, TurnoEstado.CONFIRMADO):
            raise ValidationException("Solo se pueden reasignar turnos pendientes o confirmados")

        # Obtener servicio para duración
        servicio = await self.servicio_repo.get_by_id(turno.servicio_id)
        if not servicio:
            raise NotFoundException("Servicio", "no encontrado")

        # Calcular nueva fecha/hora fin
        nueva_fecha_inicio = datetime.combine(nueva_fecha, nueva_hora_inicio).replace(tzinfo=UTC)
        nueva_fecha_fin = nueva_fecha_inicio + timedelta(minutes=servicio.duracion_min)

        if nueva_fecha_inicio <= ahora_negocio():
            raise ValidationException("No se puede reasignar un turno al pasado")

        async with _reserva_locks[profesional_id]:
            # El propio turno no debe bloquear su nuevo horario
            libre = all(
                t.id == turno_id
                or not (nueva_fecha_inicio < _aware(t.fecha_fin) and nueva_fecha_fin > _aware(t.fecha_inicio))
                for t in await self.turno_repo.get_turnos_ocupados(
                    profesional_id, nueva_fecha_inicio.date(), nueva_fecha_fin.date()
                )
            )
            if not libre:
                raise ConflictException("El nuevo slot seleccionado ya no está disponible")

            turno_reasignado = await self.turno_repo.reasignar(
                turno_id=turno_id,
                nueva_fecha_inicio=nueva_fecha_inicio,
                nueva_fecha_fin=nueva_fecha_fin,
                motivo=motivo,
            )
            await self.session.commit()

        return TurnoResponse.model_validate(turno_reasignado)

    async def agregar_notas_profesional(
        self, turno_id: int, profesional_id: int, notas: str
    ) -> TurnoResponse:
        """Agregar/actualizar notas internas del profesional."""
        turno = await self.turno_repo.get_by_id(turno_id)
        if not turno:
            raise NotFoundException("Turno", turno_id)

        if turno.profesional_id != profesional_id:
            raise NotFoundException("Turno", turno_id)

        turno_actualizado = await self.turno_repo.agregar_notas(turno_id, notas)
        return TurnoResponse.model_validate(turno_actualizado)

    async def crear_turno_desde_chatbot(
        self, data: ChatbotReservarRequest
    ) -> ChatbotReservarResponse:
        """
        Crear turno desde chatbot (endpoint interno).

        Reusa las mismas validaciones que crear_reserva_manual.
        """
        # Convertir a formato interno
        turno_response = await self.crear_reserva_manual(
            cliente_id=data.cliente_id,
            profesional_id=data.profesional_id,
            servicio_id=data.servicio_id,
            fecha=data.fecha,
            hora_inicio=data.hora_inicio,
        )

        # Obtener nombres para respuesta conversacional
        profesional = await self.prof_repo.get_by_id(data.profesional_id)
        servicio = await self.servicio_repo.get_by_id(data.servicio_id)

        return ChatbotReservarResponse(
            turno_id=turno_response.id,
            estado=turno_response.estado,
            profesional_nombre=f"{profesional.nombre} {profesional.apellido}" if profesional else "Desconocido",
            servicio_nombre=servicio.nombre if servicio else "Desconocido",
            fecha=data.fecha,
            hora_inicio=data.hora_inicio,
            hora_fin=turno_response.fecha_fin.timetz() if hasattr(turno_response.fecha_fin, 'timetz') else time(
                turno_response.fecha_fin.hour, turno_response.fecha_fin.minute
            ),
        )

    async def get_turnos_by_cliente(
        self, cliente_id: int, filtros: TurnoFiltros
    ) -> tuple[list[TurnoResponse], int]:
        """Get turnos for a cliente with pagination."""
        turnos, total = await self.turno_repo.get_by_cliente(cliente_id, filtros)
        return [TurnoResponse.model_validate(t) for t in turnos], total

    async def get_turnos_by_profesional(
        self, profesional_id: int, filtros: TurnoFiltros
    ) -> tuple[list[TurnoResponse], int]:
        """Get turnos for a profesional with pagination."""
        turnos, total = await self.turno_repo.get_by_profesional(profesional_id, filtros)
        return [TurnoResponse.model_validate(t) for t in turnos], total

    async def get_turno_by_id(self, turno_id: int) -> TurnoResponse | None:
        """Get single turno by ID."""
        turno = await self.turno_repo.get_by_id(turno_id)
        if not turno:
            return None
        return TurnoResponse.model_validate(turno)

    # =========================================================================
    # Admin methods (no ownership filter)
    # =========================================================================

    async def get_all_turnos_admin(
        self,
        page: int,
        size: int,
        estado: str | None = None,
        desde: date | None = None,
        hasta: date | None = None,
        profesional_id: int | None = None,
        cliente_id: int | None = None,
    ) -> tuple[list[TurnoResponse], int]:
        """Get all turnos with pagination and filters (Admin)."""
        turnos, total = await self.turno_repo.get_all_paginated(
            page=page,
            size=size,
            estado=estado,
            desde=desde,
            hasta=hasta,
            profesional_id=profesional_id,
            cliente_id=cliente_id,
        )
        return [TurnoResponse.model_validate(t) for t in turnos], total

    async def get_turno_by_id_admin(self, turno_id: int) -> TurnoResponse | None:
        """Get single turno by ID (Admin - no ownership check)."""
        turno = await self.turno_repo.get_by_id_admin(turno_id)
        if not turno:
            return None
        return TurnoResponse.model_validate(turno)
