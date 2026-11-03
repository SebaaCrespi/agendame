import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.profesional import Profesional


class UserRole(str, enum.Enum):
    """User roles in the system."""

    CLIENTE = "CLIENTE"
    PROVEEDOR = "PROVEEDOR"
    ADMIN = "ADMIN"


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    rol: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, create_constraint=True),
        default=UserRole.CLIENTE,
        nullable=False,
    )
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships (using string forward refs to avoid circular imports)
    profesional: Mapped[Optional["Profesional"]] = relationship(
        "Profesional",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )
    cliente: Mapped[Optional["Cliente"]] = relationship(
        "Cliente",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    # Table constraints and indexes
    __table_args__ = (
        Index("ix_users_email_activo", "email", "activo"),
        Index("ix_users_rol_activo", "rol", "activo"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', rol={self.rol.value})>"


class RefreshToken(Base):
    """Refresh token model for JWT token rotation."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    # Table constraints
    __table_args__ = (
        Index("ix_refresh_tokens_user_expires", "user_id", "expires_at"),
        Index("ix_refresh_tokens_hash_revoked", "token_hash", "revoked_at"),
    )

    def is_valid(self) -> bool:
        """Check if the refresh token is still valid (not expired, not revoked)."""
        now = datetime.now(UTC)
        expires_at = self.expires_at
        # Ensure expires_at is timezone-aware for comparison
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return self.revoked_at is None and expires_at > now

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, valid={self.is_valid()})>"
