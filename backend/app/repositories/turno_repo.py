"""Turno Repository - Data access layer for Turno model."""

from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cliente import Cliente
from app.models.turno import Turno, TurnoEstado
from app.schemas.turno import TurnoFiltros

if TYPE_CHECKING:
    pass


class TurnoRepo:
    """Repository for Turno data access."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, turno_id: int) -> Turno | None:
        """Get turno by ID with relationships loaded."""
        stmt = (
            select(Turno)
            .where(Turno.id == turno_id)
            .options(
                selectinload(Turno.profesional),
                selectinload(Turno.cliente),
                selectinload(Turno.servicio),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_cliente(
        self, cliente_id: int, filtros: TurnoFiltros
    ) -> tuple[list[Turno], int]:
        """Get turnos for a cliente with pagination and filters."""
        # Base query
        stmt = select(Turno).where(Turno.cliente_id == cliente_id)

        # Apply filters
        if filtros.estado:
            stmt = stmt.where(Turno.estado == TurnoEstado(filtros.estado))
        if filtros.desde:
            desde_dt = datetime.combine(filtros.desde, time.min).replace(tzinfo=UTC)
            stmt = stmt.where(Turno.fecha_inicio >= desde_dt)
        if filtros.hasta:
            hasta_dt = datetime.combine(filtros.hasta, time.max).replace(tzinfo=UTC)
            stmt = stmt.where(Turno.fecha_inicio <= hasta_dt)

        # Order by fecha_inicio desc (most recent first)
        stmt = stmt.order_by(Turno.fecha_inicio.desc())

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Pagination
        offset = (filtros.page - 1) * filtros.size
        stmt = stmt.offset(offset).limit(filtros.size)

        # Execute with relationships
        stmt = stmt.options(
            selectinload(Turno.profesional),
            selectinload(Turno.servicio),
        )
        result = await self.session.execute(stmt)
        turnos = list(result.scalars().all())

        return turnos, total

    async def get_by_profesional(
        self, profesional_id: int, filtros: TurnoFiltros
    ) -> tuple[list[Turno], int]:
        """Get turnos for a profesional with pagination and filters."""
        # Base query
        stmt = select(Turno).where(Turno.profesional_id == profesional_id)

        # Apply filters
        if filtros.estado:
            stmt = stmt.where(Turno.estado == TurnoEstado(filtros.estado))
        if filtros.desde:
            desde_dt = datetime.combine(filtros.desde, time.min).replace(tzinfo=UTC)
            stmt = stmt.where(Turno.fecha_inicio >= desde_dt)
        if filtros.hasta:
            hasta_dt = datetime.combine(filtros.hasta, time.max).replace(tzinfo=UTC)
            stmt = stmt.where(Turno.fecha_inicio <= hasta_dt)

        # Order by fecha_inicio asc (chronological for grilla)
        stmt = stmt.order_by(Turno.fecha_inicio.asc())

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Pagination
        offset = (filtros.page - 1) * filtros.size
        stmt = stmt.offset(offset).limit(filtros.size)

        # Execute with relationships
        stmt = stmt.options(
            selectinload(Turno.cliente),
            selectinload(Turno.servicio),
        )
        result = await self.session.execute(stmt)
        turnos = list(result.scalars().all())

        return turnos, total

    async def get_turnos_ocupados(
        self, profesional_id: int, desde: date, hasta: date
    ) -> list[Turno]:
        """Get turnos that block slots (CONFIRMADO, PENDIENTE, EN_CURSO)."""
        desde_dt = datetime.combine(desde, time.min).replace(tzinfo=UTC)
        hasta_dt = datetime.combine(hasta, time.max).replace(tzinfo=UTC)

        stmt = select(Turno).where(
            Turno.profesional_id == profesional_id,
            Turno.estado.in_([
                TurnoEstado.CONFIRMADO,
                TurnoEstado.PENDIENTE,
                TurnoEstado.EN_CURSO,
            ]),
            Turno.fecha_inicio >= desde_dt,
            Turno.fecha_inicio <= hasta_dt,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def crear_turno(self, data: dict[str, Any]) -> Turno:
        """Create a new turno."""
        turno = Turno(**data)
        self.session.add(turno)
        await self.session.flush()
        await self.session.refresh(turno)
        return turno

    async def actualizar_estado(
        self, turno_id: int, nuevo_estado: TurnoEstado, timestamp_campo: str | None
    ) -> Turno | None:
        """Update turno state and corresponding timestamp."""
        turno = await self.get_by_id(turno_id)
        if not turno:
            return None

        turno.estado = nuevo_estado
        if timestamp_campo:
            setattr(turno, timestamp_campo, datetime.now(UTC))

        await self.session.flush()
        await self.session.refresh(turno)
        return turno

    async def reasignar(
        self,
        turno_id: int,
        nueva_fecha_inicio: datetime,
        nueva_fecha_fin: datetime,
        motivo: str,
    ) -> Turno | None:
        """Reassign turno to new datetime."""
        turno = await self.get_by_id(turno_id)
        if not turno:
            return None

        # Store old values for audit (could be logged separately)
        _ = turno.fecha_inicio
        _ = turno.fecha_fin

        turno.fecha_inicio = nueva_fecha_inicio
        turno.fecha_fin = nueva_fecha_fin
        # Could add audit log here if needed
        # For now, we could store in notas_profesional or a separate audit table

        await self.session.flush()
        await self.session.refresh(turno)
        return turno

    async def agregar_notas(self, turno_id: int, notas_profesional: str) -> Turno | None:
        """Update profesional notes on a turno."""
        turno = await self.get_by_id(turno_id)
        if not turno:
            return None

        turno.notas_profesional = notas_profesional
        await self.session.flush()
        await self.session.refresh(turno)
        return turno

    async def cancelar(
        self,
        turno_id: int,
        cancelado_por: str,
        motivo: str,
        timestamp: datetime,
    ) -> Turno | None:
        """Cancel a turno."""
        turno = await self.get_by_id(turno_id)
        if not turno:
            return None

        if cancelado_por == "cliente":
            turno.estado = TurnoEstado.CANCELADO_CLIENTE
        elif cancelado_por == "profesional":
            turno.estado = TurnoEstado.CANCELADO_PROFESIONAL
        else:
            raise ValueError(f"Invalid cancelado_por: {cancelado_por}")

        turno.cancelado_por = cancelado_por
        turno.motivo_cancelacion = motivo
        turno.cancelado_en = timestamp

        await self.session.flush()
        await self.session.refresh(turno)
        return turno

    # =========================================================================
    # Admin methods (no ownership filter)
    # =========================================================================

    async def get_all_paginated(
        self,
        page: int,
        size: int,
        estado: str | None = None,
        desde: date | None = None,
        hasta: date | None = None,
        profesional_id: int | None = None,
        cliente_id: int | None = None,
    ) -> tuple[list[Turno], int]:
        """Get all turnos with pagination and filters (Admin)."""

        stmt = select(Turno)

        # Apply filters
        if estado:
            stmt = stmt.where(Turno.estado == TurnoEstado(estado))
        if profesional_id:
            stmt = stmt.where(Turno.profesional_id == profesional_id)
        if cliente_id:
            stmt = stmt.where(Turno.cliente_id == cliente_id)
        if desde:
            desde_dt = datetime.combine(desde, time.min).replace(tzinfo=UTC)
            stmt = stmt.where(Turno.fecha_inicio >= desde_dt)
        if hasta:
            hasta_dt = datetime.combine(hasta, time.max).replace(tzinfo=UTC)
            stmt = stmt.where(Turno.fecha_inicio <= hasta_dt)

        # Order by fecha_inicio desc (most recent first)
        stmt = stmt.order_by(Turno.fecha_inicio.desc())

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Pagination
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size)

        # Execute with relationships
        stmt = stmt.options(
            selectinload(Turno.profesional),
            selectinload(Turno.cliente).selectinload(Cliente.user),
            selectinload(Turno.servicio),
        )
        result = await self.session.execute(stmt)
        turnos = list(result.scalars().all())

        return turnos, total

    async def get_by_id_admin(self, turno_id: int) -> Turno | None:
        """Get turno by ID with all relationships (Admin - no ownership check)."""
        from app.models.cliente import Cliente

        stmt = (
            select(Turno)
            .where(Turno.id == turno_id)
            .options(
                selectinload(Turno.profesional),
                selectinload(Turno.cliente).selectinload(Cliente.user),
                selectinload(Turno.servicio),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
