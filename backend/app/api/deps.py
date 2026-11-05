"""FastAPI dependencies for authentication, authorization, and rate limiting."""


from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UnauthorizedException
from app.core.security import verify_token
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepo

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT access token.

    Args:
        credentials: HTTP Bearer credentials
        session: Database session

    Returns:
        Current user

    Raises:
        HTTPException: 401 if not authenticated or token invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify token and get user ID
        payload = verify_token(credentials.credentials, token_type="access")
        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("Token sin subject")

        # Get user from database
        repo = UserRepo(session)
        user = await repo.get_by_id(int(user_id))

        if user is None or not user.activo:
            raise UnauthorizedException("Usuario no encontrado o inactivo")

        # Verify role matches token
        if user.rol.value != payload.get("rol"):
            raise UnauthorizedException("Token inválido: rol no coincide")

        return user

    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> User | None:
    """Usuario autenticado, o None si no se envió token (un token inválido sigue dando 401)."""
    if credentials is None:
        return None
    return await get_current_user(credentials, session)


def require_roles(*allowed_roles: UserRole) -> Callable[[User], Coroutine[Any, Any, User]]:
    """Dependency that checks if current user has one of the allowed roles.

    Args:
        *allowed_roles: Allowed UserRole values

    Returns:
        Dependency that returns current user if authorized

    Raises:
        HTTPException: 403 if user role not in allowed roles
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: se requiere rol {', '.join(r.value for r in allowed_roles)}",
            )
        return current_user

    return role_checker


# Convenience dependencies for common role combinations
require_admin = require_roles(UserRole.ADMIN)
require_proveedor = require_roles(UserRole.PROVEEDOR, UserRole.ADMIN)
require_cliente = require_roles(UserRole.CLIENTE, UserRole.ADMIN)
require_proveedor_or_admin = require_roles(UserRole.PROVEEDOR, UserRole.ADMIN)


async def get_current_profesional(
    current_user: User = Depends(require_proveedor),
) -> User:
    """Get current user as profesional (requires PROVEEDOR or ADMIN role).

    This is a placeholder for when Profesional model is fully implemented.
    Currently just verifies the user has the right role.

    Args:
        current_user: Current authenticated user with PROVEEDOR or ADMIN role

    Returns:
        Current user

    Raises:
        HTTPException: 403 if user is not a profesional
    """
    # TODO: When Profesional model is implemented, load and return the Profesional entity
    # For now, just return the user with role verification
    return current_user


async def get_current_cliente(
    current_user: User = Depends(require_cliente),
) -> User:
    """Get current user as cliente (requires CLIENTE or ADMIN role).

    This is a placeholder for when Cliente model is fully implemented.

    Args:
        current_user: Current authenticated user with CLIENTE or ADMIN role

    Returns:
        Current user
    """
    # TODO: When Cliente model is implemented, load and return the Cliente entity
    return current_user


def get_rate_limiter() -> Limiter:
    """Get the rate limiter instance."""
    return limiter


class RateLimitDependency:
    """Dependency for applying rate limits to specific endpoints."""

    def __init__(self, limit: str = "5/minute"):
        self.limit = limit

    async def __call__(self, request: Request) -> None:
        """Apply rate limit to request."""
        # The actual limiting is done by slowapi middleware
        # This dependency is a placeholder for documentation
        pass


# Pre-configured rate limiters for auth endpoints
auth_rate_limit = RateLimitDependency("5/minute")


# Re-export get_db for convenience (already imported at top)
get_db_dependency = get_db

__all__ = [
    "get_db_dependency",
]
