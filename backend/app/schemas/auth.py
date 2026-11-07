"""Pydantic schemas for authentication endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserRegister(BaseModel):
    """Schema for user registration request."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "email": "usuario@ejemplo.com",
                "password": "mipassword123",
                "nombre": "Juan Pérez",
                "rol": "CLIENTE",
            }
        },
    )

    email: EmailStr = Field(description="Email del usuario (único)")
    password: str = Field(min_length=8, max_length=128, description="Contraseña (mín 8 caracteres)")
    nombre: str = Field(min_length=1, max_length=100, description="Nombre completo")
    rol: UserRole = Field(default=UserRole.CLIENTE, description="Rol del usuario")

    @field_validator("password")
    @classmethod
    def password_not_common(cls, v: str) -> str:
        """Basic password strength check."""
        common_passwords = {
            "password", "12345678", "password123", "admin123", "qwerty123"
        }
        if v.lower() in common_passwords:
            raise ValueError("La contraseña es demasiado común")
        return v


class UserLogin(BaseModel):
    """Schema for user login request."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "usuario@ejemplo.com",
                "password": "mipassword123",
            }
        },
    )

    email: EmailStr = Field(description="Email del usuario")
    password: str = Field(description="Contraseña")


class TokenResponse(BaseModel):
    """Schema for token response (access + refresh)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": 1,
                    "email": "usuario@ejemplo.com",
                    "nombre": "Juan Pérez",
                    "rol": "CLIENTE",
                    "activo": True,
                    "created_at": "2024-01-15T10:30:00Z",
                },
            }
        },
    )

    access_token: str = Field(description="JWT access token (24h)")
    refresh_token: str = Field(description="JWT refresh token (7d, rotativo)")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(description="Segundos hasta expiración del access token")
    user: "UserResponse" = Field(description="Datos del usuario autenticado")


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        },
    )

    refresh_token: str = Field(description="Refresh token válido")


class UserResponse(BaseModel):
    """Schema for user response (without password)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "usuario@ejemplo.com",
                "nombre": "Juan Pérez",
                "rol": "CLIENTE",
                "activo": True,
                "created_at": "2024-01-15T10:30:00Z",
            }
        },
    )

    id: int
    email: EmailStr
    nombre: str
    rol: UserRole
    activo: bool
    created_at: datetime


class UserUpdate(BaseModel):
    """Schema for user profile update request."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "nombre": "Juan Pérez Actualizado",
                "password": "nuevapassword123",
            }
        },
    )

    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_not_common(cls, v: str | None) -> str | None:
        """Basic password strength check."""
        if v is not None:
            common_passwords = {
                "password", "12345678", "password123", "admin123", "qwerty123"
            }
            if v.lower() in common_passwords:
                raise ValueError("La contraseña es demasiado común")
        return v


# Resolve forward reference
TokenResponse.model_rebuild()
