"""Authentication service with business logic for auth operations."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_role,
    get_token_subject,
    hash_password,
    hash_token,
)
from app.models.user import RefreshToken, User
from app.repositories.user_repo import UserRepo
from app.schemas.auth import TokenResponse, UserRegister, UserUpdate


class AuthService:
    """Service layer for authentication operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepo(session)

    async def register(self, data: UserRegister) -> tuple[User, str, str]:
        """Register a new user.

        Args:
            data: Registration data

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            ConflictException: If email already exists
        """
        # Check if email already exists
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ConflictException("Email ya registrado")

        # Create user
        user = await self.repo.create(
            email=data.email,
            password=data.password,
            nombre=data.nombre,
            rol=data.rol,
        )

        # Generate tokens
        access_token, refresh_token = await self._generate_tokens(user)

        return user, access_token, refresh_token

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        """Authenticate user and generate tokens.

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            UnauthorizedException: If credentials are invalid
            ForbiddenException: If user is inactive
        """
        user = await self.repo.get_by_email(email)
        if user is None:
            raise UnauthorizedException("Credenciales inválidas")

        if not user.activo:
            raise ForbiddenException("Usuario inactivo")

        if not await self.repo.verify_password(user, password):
            raise UnauthorizedException("Credenciales inválidas")

        # Generate tokens
        access_token, refresh_token = await self._generate_tokens(user)

        return user, access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """Refresh access token using a valid refresh token (with rotation).

        Args:
            refresh_token: Current refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token)

        Raises:
            UnauthorizedException: If refresh token is invalid, expired, or reused
        """
        # Decode token to get subject and hash
        try:
            payload = decode_token(refresh_token)
        except Exception as e:
            raise UnauthorizedException(f"Token inválido: {str(e)}") from None

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Tipo de token incorrecto")

        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("Token sin subject")

        # Hash the provided token to look it up in DB
        token_hash = hash_token(refresh_token)

        # Get the stored refresh token
        stored_token = await self.repo.get_valid_refresh_token(token_hash)
        if stored_token is None:
            # Check if token exists but was revoked (rotation reuse detection)
            stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing is not None and existing.revoked_at is not None:
                # Token was already used (rotation reuse) - revoke all user tokens
                await self.repo.revoke_all_user_tokens(int(user_id))
                raise UnauthorizedException("Token inválido: reutilización detectada")

            raise UnauthorizedException("Refresh token expirado o inválido")

        # Revoke the current token (rotation)
        await self.repo.revoke_refresh_token(token_hash)

        # Get user
        user = await self.repo.get_by_id(int(user_id))
        if user is None or not user.activo:
            raise UnauthorizedException("Usuario no encontrado o inactivo")

        # Generate new token pair
        new_access, new_refresh = await self._generate_tokens(user)

        return new_access, new_refresh

    async def get_current_user(self, access_token: str) -> User:
        """Get current user from access token.

        Args:
            access_token: JWT access token

        Returns:
            User object

        Raises:
            UnauthorizedException: If token is invalid or user not found
        """
        try:
            user_id = get_token_subject(access_token)
            role = get_token_role(access_token)
        except Exception as e:
            raise UnauthorizedException(f"Token inválido: {str(e)}") from None

        user = await self.repo.get_by_id(user_id)
        if user is None or not user.activo:
            raise UnauthorizedException("Usuario no encontrado o inactivo")

        # Verify role matches (additional security)
        if user.rol.value != role:
            raise UnauthorizedException("Token inválido: rol no coincide")

        return user

    async def update_profile(
        self, user_id: int, data: UserUpdate
    ) -> User | None:
        """Update user profile.

        Args:
            user_id: User ID
            data: Update data (nombre and/or password)

        Returns:
            Updated user or None if not found
        """
        # If password is being changed, revoke all refresh tokens
        if data.password is not None:
            await self.repo.revoke_all_user_tokens(user_id)

        return await self.repo.update(
            user_id=user_id,
            nombre=data.nombre,
            password=data.password,
        )

    async def _generate_tokens(self, user: User) -> tuple[str, str]:
        """Generate access and refresh token pair for a user.

        Args:
            user: User object

        Returns:
            Tuple of (access_token, refresh_token)
        """
        token_data = {"sub": str(user.id), "rol": user.rol.value}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Store refresh token hash in DB
        refresh_token_hash = hash_password(refresh_token)
        expires_at = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self.repo.create_refresh_token(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=expires_at,
        )

        return access_token, refresh_token

    @staticmethod
    def build_token_response(
        user: User, access_token: str, refresh_token: str
    ) -> TokenResponse:
        """Build TokenResponse schema from user and tokens."""
        from app.schemas.auth import UserResponse

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )
