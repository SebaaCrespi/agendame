"""Cliente model."""

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.turno import Turno
    from app.models.user import User


class Cliente(Base):
    """Modelo de cliente (extensión de User con datos específicos)."""

    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    preferencias: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)  # Futuro: notificaciones, etc.
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="cliente", lazy="selectin")
    turnos: Mapped[list["Turno"]] = relationship(
        "Turno",
        back_populates="cliente",
        lazy="selectin",
    )

    # Table constraints and indexes
    __table_args__ = (
        Index("ix_cliente_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<Cliente(id={self.id}, user_id={self.user_id})>"
