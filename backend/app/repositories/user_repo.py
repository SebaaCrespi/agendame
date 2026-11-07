"""User repository for data access operations."""

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password, verify_password
from app.models.cliente import Cliente
from app.models.user import RefreshToken, User, UserRole


class UserRepo:
    """Repository for User and RefreshToken operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        email: str,
        password: str,
        nombre: str,
        rol: UserRole = UserRole.CLIENTE,
    ) -> User:
        """Create a new user with hashed password."""
        password_hash = hash_password(password)
        user = User(
            email=email.lower(),
            password_hash=password_hash,
            nombre=nombre,
            rol=rol,
        )
        self.session.add(user)
        await self.session.flush()
        if rol == UserRole.CLIENTE:
            # Every CLIENTE needs a Cliente profile to book turnos
            self.session.add(Cliente(user_id=user.id))
            await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID with relationships loaded."""
        stmt = (
            select(User)
            .options(
                selectinload(User.profesional),
                selectinload(User.cliente),
            )
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email with relationships loaded."""
        stmt = (
            select(User)
            .options(
                selectinload(User.profesional),
                selectinload(User.cliente),
            )
            .where(User.email == email.lower())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        user_id: int,
        nombre: str | None = None,
        password: str | None = None,
    ) -> User | None:
        """Update user profile (nombre and/or password)."""
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        if nombre is not None:
            user.nombre = nombre

        if password is not None:
            user.password_hash = hash_password(password)

        user.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def verify_password(self, user: User, password: str) -> bool:
        """Verify user's password."""
        return verify_password(password, user.password_hash)

    # Refresh Token operations

    async def create_refresh_token(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Store a new refresh token hash."""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(refresh_token)
        await self.session.flush()
        await self.session.refresh(refresh_token)
        return refresh_token

    async def get_valid_refresh_token(self, token_hash: str) -> RefreshToken | None:
        """Get a valid (not expired, not revoked) refresh token by hash."""
        # Use naive UTC datetime for comparison with SQLite-stored naive datetimes
        now = datetime.now(UTC).replace(tzinfo=None)
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> bool:
        """Revoke a refresh token by setting revoked_at timestamp."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked_at=datetime.now(UTC))
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user (e.g., on password change)."""
        now = datetime.now(UTC)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def get_user_active_refresh_tokens(self, user_id: int) -> list[RefreshToken]:
        """Get all active (not revoked, not expired) refresh tokens for a user."""
        now = datetime.now(UTC)
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
