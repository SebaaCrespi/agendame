"""Core module exports."""

from app.core.config import Settings, get_settings, settings
from app.core.database import Base, async_session_maker, close_db, engine, get_db, init_db
from app.core.exceptions import (
    AppException,
    BusinessException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ProblemDetail,
    TooManyRequestsException,
    UnauthorizedException,
    ValidationException,
    generic_exception_handler,
    http_exception_handler,
    register_exception_handlers,
    validation_exception_handler,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_role,
    get_token_subject,
    hash_password,
    verify_password,
    verify_token,
)

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "settings",
    # Database
    "Base",
    "engine",
    "async_session_maker",
    "get_db",
    "init_db",
    "close_db",
    # Security
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
    "get_token_subject",
    "get_token_role",
    # Exceptions
    "ProblemDetail",
    "AppException",
    "ValidationException",
    "NotFoundException",
    "ConflictException",
    "UnauthorizedException",
    "ForbiddenException",
    "TooManyRequestsException",
    "BusinessException",
    "register_exception_handlers",
    "app_exception_handler",
    "http_exception_handler",
    "validation_exception_handler",
    "generic_exception_handler",
]
