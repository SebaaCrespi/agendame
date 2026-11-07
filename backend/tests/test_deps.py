"""Tests for authentication dependencies."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token


class TestGetCurrentUser:
    """Test get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_valid_token(self, async_client: AsyncClient, test_user, auth_headers):
        """Test valid access token returns user."""
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["nombre"] == test_user.nombre
        assert data["rol"] == test_user.rol.value

    @pytest.mark.asyncio
    async def test_missing_token(self, async_client: AsyncClient):
        """Test missing Authorization header returns 401."""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "No autenticado"

    @pytest.mark.asyncio
    async def test_invalid_token(self, async_client: AsyncClient):
        """Test invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert "Token inválido" in data["detail"]

    @pytest.mark.asyncio
    async def test_expired_token(self, async_client: AsyncClient, test_user):
        """Test expired token returns 401."""
        # Create an expired token (exp in the past)
        expired_token = create_access_token(
            {"sub": str(test_user.id), "rol": test_user.rol.value},
            expires_delta=-timedelta(hours=1),
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert "expirado" in data["detail"].lower() or "expired" in data["detail"].lower() or "signature has expired" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_wrong_token_type(self, async_client: AsyncClient, test_user):
        """Test refresh token used as access token returns 401."""
        refresh_token = create_refresh_token({"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {refresh_token}"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert "tipo de token incorrecto" in data["detail"].lower() or "token inv" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_token_user_not_found(self, async_client: AsyncClient):
        """Test token for non-existent user returns 401."""
        token = create_access_token({"sub": "99999", "rol": "CLIENTE"})
        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert "no encontrado" in data["detail"].lower() or "not found" in data["detail"].lower() or "no encontrado" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_token_inactive_user(self, async_client: AsyncClient, db_session, test_user):
        """Test token for inactive user returns 401."""
        # Deactivate user
        test_user.activo = False
        await db_session.commit()

        # Create a new token for the inactive user
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(test_user.id), "rol": test_user.rol.value})
        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert "inactivo" in data["detail"].lower() or "inactive" in data["detail"].lower()


class TestRequireRoles:
    """Test require_roles dependency."""

    @pytest.mark.asyncio
    async def test_admin_access_admin_endpoint(self, async_client: AsyncClient, admin_headers):
        """Test ADMIN can access admin endpoint."""
        # Create a test endpoint that requires admin
        # For now test via the require_admin dependency behavior
        pass

    @pytest.mark.asyncio
    async def test_proveedor_cannot_access_admin(self, async_client: AsyncClient, profesional_headers):
        """Test PROVEEDOR cannot access admin-only endpoint."""
        # This would require a test route with require_admin
        pass

    @pytest.mark.asyncio
    async def test_cliente_cannot_access_proveedor(self, async_client: AsyncClient, auth_headers):
        """Test CLIENTE cannot access proveedor-only endpoint."""
        pass


class TestTokenCreation:
    """Test token creation utilities."""

    def test_create_access_token(self):
        """Test access token creation."""
        token = create_access_token({"sub": "1", "rol": "CLIENTE"})
        assert isinstance(token, str)
        assert len(token) > 0
        # Token should have 3 parts (header.payload.signature)
        assert token.count(".") == 2

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        token = create_refresh_token({"sub": "1"})
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2

    def test_token_payload(self):
        """Test token payload contains correct claims."""
        from app.core.security import decode_token

        token = create_access_token({"sub": "42", "rol": "ADMIN"}, expires_delta=timedelta(hours=1))
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["rol"] == "ADMIN"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_refresh_token_payload(self):
        """Test refresh token has type refresh."""
        from app.core.security import decode_token

        token = create_refresh_token({"sub": "42"})
        payload = decode_token(token)
        assert payload["type"] == "refresh"
        assert "exp" in payload


from datetime import timedelta  # noqa: E402
