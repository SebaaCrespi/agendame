"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, limiter
from app.core.database import get_db
from app.schemas.auth import (
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService instance."""
    return AuthService(session)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="""
    Registra un nuevo usuario en el sistema.

    - **email**: Email único del usuario
    - **password**: Contraseña (mínimo 8 caracteres)
    - **nombre**: Nombre completo
    - **rol**: CLIENTE, PROVEEDOR o ADMIN (default: CLIENTE)

    Retorna access token (24h), refresh token (7d rotativo) y datos del usuario.
    """,
    responses={
        201: {"description": "Usuario creado exitosamente"},
        409: {"description": "Email ya registrado"},
        422: {"description": "Error de validación"},
        429: {"description": "Demasiadas solicitudes"},
    },
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Register a new user."""
    user, access_token, refresh_token = await auth_service.register(data)
    return auth_service.build_token_response(user, access_token, refresh_token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="""
    Autentica un usuario existente y genera tokens de acceso y renovación.

    - **email**: Email del usuario
    - **password**: Contraseña

    Retorna access token (24h), refresh token (7d rotativo) y datos del usuario.
    """,
    responses={
        200: {"description": "Login exitoso"},
        401: {"description": "Credenciales inválidas"},
        403: {"description": "Usuario inactivo"},
        422: {"description": "Error de validación"},
        429: {"description": "Demasiadas solicitudes"},
    },
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """User login."""
    user, access_token, refresh_token = await auth_service.login(data.email, data.password)
    return auth_service.build_token_response(user, access_token, refresh_token)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar access token",
    description="""
    Obtiene un nuevo access token usando un refresh token válido.

    Implementa **rotación de refresh tokens**: cada uso invalida el token anterior
    y genera un nuevo par (access + refresh).

    - **refresh_token**: Refresh token válido (no expirado, no revocado)

    Retorna nuevo access token (24h) y nuevo refresh token (7d).
    """,
    responses={
        200: {"description": "Tokens renovados exitosamente"},
        401: {"description": "Refresh token inválido, expirado o reutilizado"},
        422: {"description": "Error de validación"},
    },
)
async def refresh(
    data: TokenRefresh,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Refresh access token with rotation."""
    access_token, refresh_token = await auth_service.refresh_tokens(data.refresh_token)
    # Get user from the new access token
    user = await auth_service.get_current_user(access_token)
    return auth_service.build_token_response(user, access_token, refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener perfil del usuario actual",
    description="""
    Retorna los datos del usuario autenticado (requiere access token válido).
    """,
    responses={
        200: {"description": "Datos del usuario"},
        401: {"description": "No autenticado / Token inválido / Token expirado"},
    },
)
async def get_me(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Get current user profile."""
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Actualizar perfil del usuario actual",
    description="""
    Actualiza el perfil del usuario autenticado.

    - **nombre**: Nuevo nombre (opcional)
    - **password**: Nueva contraseña (opcional, mínimo 8 caracteres)

    Si se cambia la contraseña, se revocan todos los refresh tokens del usuario.
    """,
    responses={
        200: {"description": "Perfil actualizado"},
        401: {"description": "No autenticado / Token inválido"},
        422: {"description": "Error de validación"},
    },
)
async def update_me(
    data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Update current user profile."""
    updated_user = await auth_service.update_profile(current_user.id, data)
    if updated_user is None:
        # This shouldn't happen since get_current_user ensures user exists
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Usuario", current_user.id)

    return UserResponse.model_validate(updated_user)
