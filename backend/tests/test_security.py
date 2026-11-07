"""Unit tests for security utilities."""

from datetime import timedelta

import pytest

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
from app.models.user import UserRole


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing produces a hash."""
        password = "mypassword123"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password
        # bcrypt hash should start with $2b$
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "mypassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "mypassword123"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty(self):
        """Test verifying empty password."""
        hashed = hash_password("password123")
        assert verify_password("", hashed) is False


class TestTokenCreation:
    """Test JWT token creation."""

    def test_create_access_token(self):
        """Test creating access token."""
        token = create_access_token({"sub": "1", "rol": "CLIENTE"})
        assert isinstance(token, str)
        assert token.count(".") == 2  # JWT has 3 parts

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        token = create_refresh_token({"sub": "1"})
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_access_token_payload(self):
        """Test access token contains correct claims."""
        token = create_access_token(
            {"sub": "42", "rol": "ADMIN"},
            expires_delta=timedelta(hours=1),
        )
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["rol"] == "ADMIN"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_refresh_token_payload(self):
        """Test refresh token has type refresh."""
        token = create_refresh_token({"sub": "42"})
        payload = decode_token(token)
        assert payload["type"] == "refresh"
        assert "exp" in payload


class TestTokenVerification:
    """Test token verification."""

    def test_verify_valid_access_token(self):
        """Test verifying valid access token."""
        token = create_access_token({"sub": "1", "rol": "CLIENTE"})
        payload = verify_token(token, token_type="access")
        assert payload["sub"] == "1"
        assert payload["rol"] == "CLIENTE"

    def test_verify_valid_refresh_token(self):
        """Test verifying valid refresh token."""
        token = create_refresh_token({"sub": "1"})
        payload = verify_token(token, token_type="refresh")
        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"

    def test_verify_wrong_type(self):
        """Test verifying token with wrong type raises error."""
        token = create_access_token({"sub": "1", "rol": "CLIENTE"})
        with pytest.raises(Exception) as exc_info:
            verify_token(token, token_type="refresh")
        assert "tipo de token incorrecto" in str(exc_info.value).lower()

    def test_verify_expired_token(self):
        """Test verifying expired token raises error."""
        from datetime import timedelta
        token = create_access_token(
            {"sub": "1", "rol": "CLIENTE"},
            expires_delta=-timedelta(hours=1),  # Expired 1 hour ago
        )
        with pytest.raises(Exception) as exc_info:
            verify_token(token, token_type="access")
        assert "expirado" in str(exc_info.value).lower() or "expired" in str(exc_info.value).lower() or "signature has expired" in str(exc_info.value).lower()

    def test_verify_malformed_token(self):
        """Test verifying malformed token raises error."""
        with pytest.raises(Exception) as exc_info:
            verify_token("not.a.valid.token", token_type="access")
        assert "inválido" in str(exc_info.value).lower()

    def test_decode_token(self):
        """Test decode_token without type verification."""
        token = create_access_token({"sub": "1", "rol": "CLIENTE"})
        payload = decode_token(token)
        assert payload["sub"] == "1"
        assert payload["rol"] == "CLIENTE"


class TestTokenSubjectAndRole:
    """Test extracting subject and role from tokens."""

    def test_get_token_subject(self):
        """Test extracting subject from token."""
        token = create_access_token({"sub": "123", "rol": "CLIENTE"})
        subject = get_token_subject(token)
        assert subject == 123

    def test_get_token_subject_missing(self):
        """Test extracting subject from token without sub raises error."""
        # Create a token without 'sub' claim
        token = create_access_token({"other": "claim"})
        with pytest.raises(Exception) as exc_info:
            get_token_subject(token)
        # The error should be about missing subject or wrong token type
        assert "subject" in str(exc_info.value).lower() or "token sin subject" in str(exc_info.value).lower() or "tipo de token incorrecto" in str(exc_info.value).lower()

    def test_get_token_role(self):
        """Test extracting role from access token."""
        token = create_access_token({"sub": "1", "rol": "ADMIN"})
        role = get_token_role(token)
        assert role == "ADMIN"

    def test_get_token_role_missing(self):
        """Test extracting role from token without rol raises error."""
        # Create an access token without 'rol' claim
        token = create_access_token({"sub": "1"})
        with pytest.raises(Exception) as exc_info:
            get_token_role(token)
        # The error should be about missing role or wrong token type
        assert "rol" in str(exc_info.value).lower() or "token sin rol" in str(exc_info.value).lower() or "tipo de token incorrecto" in str(exc_info.value).lower()


class TestUserRoleEnum:
    """Test UserRole enum values."""

    def test_role_values(self):
        """Test UserRole enum values."""
        assert UserRole.CLIENTE.value == "CLIENTE"
        assert UserRole.PROVEEDOR.value == "PROVEEDOR"
        assert UserRole.ADMIN.value == "ADMIN"

    def test_role_from_string(self):
        """Test creating UserRole from string."""
        assert UserRole("CLIENTE") == UserRole.CLIENTE
        assert UserRole("PROVEEDOR") == UserRole.PROVEEDOR
        assert UserRole("ADMIN") == UserRole.ADMIN

    def test_invalid_role(self):
        """Test invalid role raises ValueError."""
        with pytest.raises(ValueError):
            UserRole("INVALID")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
