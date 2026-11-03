import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# Use bcrypt directly to avoid passlib's bcrypt detection bug
# bcrypt has a 72-byte password limit
BCRYPT_COST = 12
MAX_PASSWORD_LENGTH = 72


def _truncate_password(password: str) -> bytes:
    """Truncate password to 72 bytes for bcrypt."""
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) > MAX_PASSWORD_LENGTH:
        pwd_bytes = pwd_bytes[:MAX_PASSWORD_LENGTH]
    return pwd_bytes


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    pwd_bytes = _truncate_password(password)
    hashed = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt(BCRYPT_COST))
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    pwd_bytes = _truncate_password(plain_password)
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except ValueError:
        return False


def hash_token(token: str) -> str:
    """Create a deterministic hash of a token for storage (SHA-256).

    Used for refresh tokens where we need deterministic hashing for lookup.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in the token (must include 'sub' and 'rol')
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        data: Data to encode in the token (must include 'sub')
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Token inválido: {str(e)}") from e


def verify_token(token: str, token_type: str = "access") -> dict[str, Any]:
    """Verify a JWT token and check its type.

    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh')

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid, expired, or wrong type
    """
    payload = decode_token(token)

    # Check token type
    if payload.get("type") != token_type:
        raise JWTError(f"Tipo de token incorrecto: se esperaba '{token_type}'")

    # Check expiration (jwt.decode already validates exp, but double-check)
    exp = payload.get("exp")
    if exp is None:
        raise JWTError("Token sin expiración")

    if datetime.fromtimestamp(exp, tz=UTC) < datetime.now(UTC):
        raise JWTError("Token expirado o inválido")

    return payload


def get_token_subject(token: str) -> int:
    """Extract user ID (subject) from a token.

    Args:
        token: JWT token string

    Returns:
        User ID as integer

    Raises:
        JWTError: If token is invalid or subject missing
    """
    payload = verify_token(token, token_type="access")
    sub = payload.get("sub")
    if sub is None:
        raise JWTError("Token sin subject (user_id)")
    try:
        return int(sub)
    except (ValueError, TypeError) as e:
        raise JWTError("Subject inválido en token") from e


def get_token_role(token: str) -> str:
    """Extract user role from an access token.

    Args:
        token: JWT access token string

    Returns:
        User role string

    Raises:
        JWTError: If token is invalid or role missing
    """
    payload = verify_token(token, token_type="access")
    role = payload.get("rol")
    if role is None:
        raise JWTError("Token sin rol")
    return role
