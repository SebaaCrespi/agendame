"""Profesional, Servicio, Disponibilidad, ExcepcionDisponibilidad models."""

import enum
from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.turno import Turno
    from app.models.user import User


class DiaSemana(str, enum.Enum):
    """Días de la semana para la grilla de disponibilidad."""

    LUNES = "LUNES"
    MARTES = "MARTES"
    MIERCOLES = "MIERCOLES"
    JUEVES = "JUEVES"
    VIERNES = "VIERNES"
    SABADO = "SABADO"
    DOMINGO = "DOMINGO"


class TipoExcepcion(str, enum.Enum):
    """Tipos de excepción de disponibilidad."""

    CERRADO = "CERRADO"  # Día completo cerrado
    HORARIO_ESPECIAL = "HORARIO_ESPECIAL"  # Horario diferente al habitual


class Profesional(Base):
    """Modelo de profesional (proveedor/peluquero)."""

    __tablename__ = "profesionales"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    foto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    slot_duracion_min: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False
    )  # Granularidad base de slots (default 30 min)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profesional", lazy="selectin")
    servicios: Mapped[list["Servicio"]] = relationship(
        "Servicio",
        back_populates="profesional",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    disponibilidades: Mapped[list["Disponibilidad"]] = relationship(
        "Disponibilidad",
        back_populates="profesional",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    excepciones: Mapped[list["ExcepcionDisponibilidad"]] = relationship(
        "ExcepcionDisponibilidad",
        back_populates="profesional",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    turnos: Mapped[list["Turno"]] = relationship(
        "Turno",
        back_populates="profesional",
        lazy="selectin",
    )

    # Table constraints and indexes
    __table_args__ = (
        Index("ix_profesional_usuario_activo", "user_id", "activo"),
        Index("ix_profesional_activo_nombre", "activo", "nombre"),
        CheckConstraint("slot_duracion_min >= 10", name="ck_profesional_slot_duracion_min"),
        CheckConstraint("slot_duracion_min <= 120", name="ck_profesional_slot_duracion_max"),
    )

    @property
    def email(self) -> str:
        """Email del usuario asociado (lo usan los esquemas de admin y /me)."""
        return self.user.email

    def __repr__(self) -> str:
        return f"<Profesional(id={self.id}, nombre='{self.nombre} {self.apellido}', activo={self.activo})>"


class Servicio(Base):
    """Modelo de servicio ofrecido por un profesional."""

    __tablename__ = "servicios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profesional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    duracion_min: Mapped[int] = mapped_column(Integer, nullable=False)  # Duración en minutos
    precio: Mapped[int] = mapped_column(Integer, nullable=False)  # Precio en centavos (evita float)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Para ordenar en UI
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    profesional: Mapped["Profesional"] = relationship("Profesional", back_populates="servicios", lazy="selectin")
    turnos: Mapped[list["Turno"]] = relationship(
        "Turno",
        back_populates="servicio",
        lazy="selectin",
    )

    # Table constraints and indexes
    __table_args__ = (
        Index("ix_servicio_profesional_activo", "profesional_id", "activo"),
        UniqueConstraint("profesional_id", "nombre", name="uq_servicio_profesional_nombre"),
        CheckConstraint("duracion_min > 0", name="ck_servicio_duracion_positiva"),
        CheckConstraint("precio >= 0", name="ck_servicio_precio_no_negativo"),
        CheckConstraint("duracion_min <= 480", name="ck_servicio_duracion_maxima"),  # Max 8 horas
    )

    def __repr__(self) -> str:
        return f"<Servicio(id={self.id}, nombre='{self.nombre}', duracion={self.duracion_min}min, precio={self.precio}¢)>"


class Disponibilidad(Base):
    """Modelo de disponibilidad semanal (grilla) de un profesional."""

    __tablename__ = "disponibilidades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profesional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dia_semana: Mapped[DiaSemana] = mapped_column(
        Enum(DiaSemana, native_enum=False, create_constraint=True), nullable=False
    )
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    profesional: Mapped["Profesional"] = relationship("Profesional", back_populates="disponibilidades", lazy="selectin")

    # Table constraints and indexes
    __table_args__ = (
        Index("ix_disponibilidad_profesional_dia", "profesional_id", "dia_semana"),
        UniqueConstraint("profesional_id", "dia_semana", name="uq_disponibilidad_profesional_dia"),
        CheckConstraint("hora_inicio < hora_fin", name="ck_disponibilidad_hora_inicio_menor_fin"),
    )

    def __repr__(self) -> str:
        return f"<Disponibilidad(profesional_id={self.profesional_id}, dia={self.dia_semana.value}, {self.hora_inicio}-{self.hora_fin})>"


class ExcepcionDisponibilidad(Base):
    """Modelo de excepción de disponibilidad (día específico)."""

    __tablename__ = "excepciones_disponibilidad"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profesional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    tipo: Mapped[TipoExcepcion] = mapped_column(
        Enum(TipoExcepcion, native_enum=False, create_constraint=True), nullable=False
    )
    hora_inicio: Mapped[time | None] = mapped_column(Time, nullable=True)  # None = día cerrado
    hora_fin: Mapped[time | None] = mapped_column(Time, nullable=True)  # None = día cerrado
    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationships
    profesional: Mapped["Profesional"] = relationship("Profesional", back_populates="excepciones", lazy="selectin")

    # Table constraints and indexes
    __table_args__ = (
        Index("ix_excepcion_profesional_fecha", "profesional_id", "fecha"),
        UniqueConstraint("profesional_id", "fecha", name="uq_excepcion_profesional_fecha"),
        CheckConstraint(
            "(tipo = 'CERRADO' AND hora_inicio IS NULL AND hora_fin IS NULL) OR "
            "(tipo = 'HORARIO_ESPECIAL' AND hora_inicio IS NOT NULL AND hora_fin IS NOT NULL AND hora_inicio < hora_fin)",
            name="ck_excepcion_tipo_horario_consistente",
        ),
    )

    def __repr__(self) -> str:
        if self.tipo == TipoExcepcion.CERRADO:
            return f"<ExcepcionDisponibilidad(profesional_id={self.profesional_id}, fecha={self.fecha}, tipo=CERRADO)>"
        return f"<ExcepcionDisponibilidad(profesional_id={self.profesional_id}, fecha={self.fecha}, {self.hora_inicio}-{self.hora_fin})>"
