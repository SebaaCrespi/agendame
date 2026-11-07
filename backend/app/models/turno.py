"""Turno model for appointments."""

import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.profesional import Profesional, Servicio


class TurnoEstado(str, enum.Enum):
    """Estados posibles de un turno."""

    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    EN_CURSO = "EN_CURSO"
    FINALIZADO = "FINALIZADO"
    CANCELADO_CLIENTE = "CANCELADO_CLIENTE"
    CANCELADO_PROFESIONAL = "CANCELADO_PROFESIONAL"
    NO_ASISTIO = "NO_ASISTIO"


class Turno(Base):
    """Modelo de turno/reserva."""

    __tablename__ = "turnos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profesional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    servicio_id: Mapped[int] = mapped_column(
        ForeignKey("servicios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[TurnoEstado] = mapped_column(
        Enum(TurnoEstado, native_enum=False, create_constraint=True),
        default=TurnoEstado.PENDIENTE,
        nullable=False,
    )
    notas_cliente: Mapped[str | None] = mapped_column(Text, nullable=True)
    notas_profesional: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelado_por: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "cliente" | "profesional"
    motivo_cancelacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creado_por: Mapped[str] = mapped_column(String(20), nullable=False)  # "cliente", "profesional", "admin", "chatbot"
    confirmado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Auditoría de la última reasignación (CU-08)
    reasignado_desde: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    motivo_reasignacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    reasignado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships (NO cascade - turnos son inmutables tras FINALIZADO)
    profesional: Mapped["Profesional"] = relationship("Profesional", back_populates="turnos", lazy="selectin")
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="turnos", lazy="selectin")
    servicio: Mapped["Servicio"] = relationship("Servicio", back_populates="turnos", lazy="selectin")

    # Table constraints and indexes
    __table_args__ = (
        Index("ix_turno_profesional_fecha", "profesional_id", "fecha_inicio"),
        Index("ix_turno_cliente_fecha", "cliente_id", "fecha_inicio"),
        Index("ix_turno_estado_fecha", "estado", "fecha_inicio"),
        Index("ix_turno_servicio_fecha", "servicio_id", "fecha_inicio"),
    )

    # Datos legibles para las respuestas de la API (relaciones cargadas con selectin)
    @property
    def cliente_nombre(self) -> str:
        return self.cliente.user.nombre

    @property
    def cliente_telefono(self) -> str | None:
        return self.cliente.telefono

    @property
    def servicio_nombre(self) -> str:
        return self.servicio.nombre

    @property
    def profesional_nombre(self) -> str:
        return f"{self.profesional.nombre} {self.profesional.apellido}"

    def __repr__(self) -> str:
        return f"<Turno(id={self.id}, prof={self.profesional_id}, cliente={self.cliente_id}, {self.fecha_inicio}-{self.fecha_fin}, {self.estado.value})>"
