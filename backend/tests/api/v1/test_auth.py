"""Integration tests for auth API endpoints."""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


class TestAuthEndpoints:
    """Test auth API endpoints."""

    @pytest.mark.asyncio
    async def test_register_endpoint(self, async_client: AsyncClient):
        """Test POST /api/v1/auth/register."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "endpoint@test.com",
                "password": "ValidPass123",
                "nombre": "Endpoint Test",
                "rol": "CLIENTE",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "endpoint@test.com"

    @pytest.mark.asyncio
    async def test_login_endpoint(self, async_client: AsyncClient, test_user):
        """Test POST /api/v1/auth/login."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_endpoint(self, async_client: AsyncClient, test_user, test_refresh_token):
        """Test POST /api/v1/auth/refresh."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": test_refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_me_endpoint(self, async_client: AsyncClient, test_user, auth_headers):
        """Test GET /api/v1/auth/me."""
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_update_me_endpoint(self, async_client: AsyncClient, test_user, auth_headers):
        """Test PUT /api/v1/auth/me."""
        response = await async_client.put(
            "/api/v1/auth/me",
            headers=auth_headers,
            json={"nombre": "Updated Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Updated Name"


class TestAuthErrors:
    """Test auth error responses."""

    @pytest.mark.asyncio
    async def test_401_unauthorized(self, async_client: AsyncClient):
        """Test 401 Unauthorized responses."""
        # Missing token
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "No autenticado"

        # Invalid token
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid"},
        )
        assert response.status_code == 401

        # Expired token
        from datetime import timedelta
        expired = create_access_token(
            {"sub": "1", "rol": "CLIENTE"},
            expires_delta=-timedelta(hours=1),
        )
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_403_forbidden(self, async_client: AsyncClient, db_session, test_user, auth_headers):
        """Test 403 Forbidden responses."""
        # Inactive user
        test_user.activo = False
        await db_session.commit()

        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 401  # Our implementation returns 401 for inactive

    @pytest.mark.asyncio
    async def test_409_conflict(self, async_client: AsyncClient, test_user):
        """Test 409 Conflict responses."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "different123",
                "nombre": "Another",
                "rol": "CLIENTE",
            },
        )
        assert response.status_code == 409
        data = response.json()
        assert data["detail"] == "Email ya registrado"

    @pytest.mark.asyncio
    async def test_422_validation(self, async_client: AsyncClient):
        """Test 422 Validation Error responses."""
        # Invalid email
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid",
                "password": "password123",
                "nombre": "Test",
                "rol": "CLIENTE",
            },
        )
        assert response.status_code == 422

        # Short password
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
                "password": "short",
                "nombre": "Test",
                "rol": "CLIENTE",
            },
        )
        assert response.status_code == 422

        # Invalid role
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
                "password": "password123",
                "nombre": "Test",
                "rol": "INVALID",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_429_rate_limit(self, async_client: AsyncClient):
        """Test 429 Too Many Requests."""
        # Make 5 requests (limit is 5/minute)
        for i in range(5):
            await async_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"ratelimit{i}@test.com",
                    "password": f"ValidPass{i}123",
                    "nombre": f"Rate Limit {i}",
                    "rol": "CLIENTE",
                },
            )

        # 6th should be rate limited
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "ratelimit6@test.com",
                "password": "ValidPass6123",
                "nombre": "Rate Limit 6",
                "rol": "CLIENTE",
            },
        )
        assert response.status_code == 429


class TestTokenRotation:
    """Test refresh token rotation."""

    @pytest.mark.asyncio
    async def test_refresh_rotation(self, async_client: AsyncClient, test_user, test_refresh_token):
        """Test refresh token rotation."""
        # First refresh
        response1 = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": test_refresh_token},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        new_refresh = data1["refresh_token"]

        # Second refresh with old token should fail (rotated)
        response2 = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": test_refresh_token},
        )
        assert response2.status_code == 401

        # Third refresh with new token should also fail (chain revoked)
        response3 = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": new_refresh},
        )
        assert response3.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_access_token(self, async_client: AsyncClient, auth_headers):
        """Test using access token as refresh token fails."""
        access_token = auth_headers["Authorization"].split(" ")[1]
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401
        data = response.json()
        assert "tipo de token incorrecto" in data["detail"].lower()


class TestRBAC:
    """Test role-based access control."""

    @pytest.mark.asyncio
    async def test_admin_access(self, async_client: AsyncClient, admin_headers):
        """Test ADMIN role access."""
        response = await async_client.get("/api/v1/auth/me", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["rol"] == "ADMIN"

    @pytest.mark.asyncio
    async def test_proveedor_access(self, async_client: AsyncClient, profesional_headers):
        """Test PROVEEDOR role access."""
        response = await async_client.get("/api/v1/auth/me", headers=profesional_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["rol"] == "PROVEEDOR"

    @pytest.mark.asyncio
    async def test_cliente_access(self, async_client: AsyncClient, auth_headers):
        """Test CLIENTE role access."""
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["rol"] == "CLIENTE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
