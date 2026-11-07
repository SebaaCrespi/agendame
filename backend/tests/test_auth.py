"""Tests for authentication API endpoints."""

from datetime import UTC

import pytest
from httpx import AsyncClient

from app.core.security import create_refresh_token, hash_password


class TestRegister:
    """Test POST /api/v1/auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_cliente_success(self, async_client: AsyncClient):
        """Test successful registration as CLIENTE."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "newpassword123",
                "nombre": "New User",
                "rol": "CLIENTE",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "newuser@test.com"
        assert data["user"]["nombre"] == "New User"
        assert data["user"]["rol"] == "CLIENTE"
        assert "password" not in data["user"]

    @pytest.mark.asyncio
    async def test_register_proveedor_success(self, async_client: AsyncClient):
        """Test successful registration as PROVEEDOR."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "proveedor@test.com",
                "password": "proveepassword123",
                "nombre": "Proveedor Test",
                "rol": "PROVEEDOR",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["rol"] == "PROVEEDOR"

    @pytest.mark.asyncio
    async def test_register_admin_success(self, async_client: AsyncClient):
        """Test successful registration as ADMIN."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@test.com",
                "password": "adminpassword123",
                "nombre": "Admin Test",
                "rol": "ADMIN",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["rol"] == "ADMIN"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, async_client: AsyncClient, test_user):
        """Test registration with duplicate email returns 409."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "differentpassword123",
                "nombre": "Another User",
                "rol": "CLIENTE",
            },
        )
        assert response.status_code == 409
        data = response.json()
        assert data["detail"] == "Email ya registrado"
        assert data["title"] == "Conflict"

    @pytest.mark.asyncio
    async def test_register_short_password(self, async_client: AsyncClient):
        """Test registration with short password returns 422."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
                "password": "short",
                "nombre": "Test User",
                "rol": "CLIENTE",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client: AsyncClient):
        """Test registration with invalid email returns 422."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "validpassword123",
                "nombre": "Test User",
                "rol": "CLIENTE",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_role(self, async_client: AsyncClient):
        """Test registration with invalid role returns 422."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
                "password": "validpassword123",
                "nombre": "Test User",
                "rol": "SUPER_ADMIN",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_common_password(self, async_client: AsyncClient):
        """Test registration with common password returns 422."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
                "password": "password123",
                "nombre": "Test User",
                "rol": "CLIENTE",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, async_client: AsyncClient):
        """Test registration with missing required fields returns 422."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Test POST /api/v1/auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient, test_user):
        """Test successful login."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, async_client: AsyncClient, test_user):
        """Test login with wrong password returns 401."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Credenciales inválidas"

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with nonexistent user returns 401."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Credenciales inválidas"

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, async_client: AsyncClient, db_session, test_user):
        """Test login with inactive user returns 403."""
        test_user.activo = False
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123",
            },
        )
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Usuario inactivo"


class TestRefresh:
    """Test POST /api/v1/auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_success(self, async_client: AsyncClient, test_user, test_refresh_token):
        """Test successful token refresh with rotation."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": test_refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert "refresh_token" in data
        # New tokens should be different from old ones
        assert data["access_token"] != test_refresh_token
        assert data["refresh_token"] != test_refresh_token

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, async_client: AsyncClient):
        """Test refresh with invalid token returns 401."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "inválido" in data["detail"].lower() or "invalid" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_refresh_expired_token(self, async_client: AsyncClient, test_user):
        """Test refresh with expired token returns 401."""
        from datetime import timedelta
        expired_refresh = create_refresh_token(
            {"sub": str(test_user.id)},
            expires_delta=-timedelta(days=1),
        )
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_refresh},
        )
        assert response.status_code == 401
        data = response.json()
        assert "expirado" in data["detail"].lower() or "expired" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_refresh_reused_token(self, async_client: AsyncClient, test_user, test_refresh_token):
        """Test refresh with already-used token returns 401 and revokes chain."""
        # First refresh - should succeed
        response1 = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": test_refresh_token},
        )
        assert response1.status_code == 200
        new_refresh = response1.json()["refresh_token"]

        # Second refresh with same (now revoked) token - should fail
        response2 = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": test_refresh_token},
        )
        assert response2.status_code == 401
        data = response2.json()
        assert "reutiliz" in data["detail"].lower() or "reuse" in data["detail"].lower()

        # Third refresh with the new token should also fail (chain revoked)
        response3 = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": new_refresh},
        )
        assert response3.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_access_token_as_refresh(self, async_client: AsyncClient, test_user, auth_headers):
        """Test using access token as refresh token returns 401."""
        access_token = auth_headers["Authorization"].split(" ")[1]
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401
        data = response.json()
        assert "tipo de token incorrecto" in data["detail"].lower()


class TestMe:
    """Test GET /api/v1/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_me_success(self, async_client: AsyncClient, test_user, auth_headers):
        """Test getting current user profile."""
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["nombre"] == test_user.nombre
        assert data["rol"] == test_user.rol.value
        assert data["activo"] is True

    @pytest.mark.asyncio
    async def test_me_no_auth(self, async_client: AsyncClient):
        """Test getting profile without auth returns 401."""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_invalid_token(self, async_client: AsyncClient):
        """Test getting profile with invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid.token"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


class TestUpdateMe:
    """Test PUT /api/v1/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_update_nombre(self, async_client: AsyncClient, test_user, auth_headers):
        """Test updating user nombre."""
        response = await async_client.put(
            "/api/v1/auth/me",
            headers=auth_headers,
            json={"nombre": "Updated Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_password(self, async_client: AsyncClient, test_user, auth_headers, db_session):
        """Test updating user password revokes refresh tokens."""
        # First, get a refresh token
        from app.core.security import create_refresh_token
        refresh_token = create_refresh_token({"sub": str(test_user.id)})
        token_hash = hash_password(refresh_token)
        from datetime import datetime, timedelta
        expires_at = datetime.now(UTC) + timedelta(days=7)

        from app.repositories.user_repo import UserRepo
        repo = UserRepo(db_session)
        await repo.create_refresh_token(test_user.id, token_hash, expires_at)
        await db_session.commit()

        # Update password
        response = await async_client.put(
            "/api/v1/auth/me",
            headers=auth_headers,
            json={"password": "newpassword123"},
        )
        assert response.status_code == 200

        # Verify old refresh token is revoked
        from sqlalchemy import select

        from app.models.user import RefreshToken
        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        assert stored is not None
        assert stored.revoked_at is not None

    @pytest.mark.asyncio
    async def test_update_invalid_password(self, async_client: AsyncClient, test_user, auth_headers):
        """Test updating with invalid password returns 422."""
        response = await async_client.put(
            "/api/v1/auth/me",
            headers=auth_headers,
            json={"password": "short"},
        )
        assert response.status_code == 422


class TestRateLimiting:
    """Test rate limiting on auth endpoints."""

    @pytest.mark.asyncio
    async def test_register_rate_limit(self, async_client: AsyncClient):
        """Test rate limit on register endpoint."""
        # Make 5 requests (should succeed)
        for i in range(5):
            response = await async_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"ratelimit{i}@test.com",
                    "password": f"ValidPass{i}123",
                    "nombre": f"Rate Limit {i}",
                    "rol": "CLIENTE",
                },
            )
            assert response.status_code == 201

        # 6th request should be rate limited
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

    @pytest.mark.asyncio
    async def test_login_rate_limit(self, async_client: AsyncClient, test_user):
        """Test rate limit on login endpoint."""
        # Read the email up front: failed logins roll back the shared session
        email = test_user.email
        # Make 5 requests (should succeed)
        for _ in range(5):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": email,
                    "password": "wrongpassword",  # Will fail but count towards rate limit
                },
            )
            # Some will be 401, but not 429

        # 6th request should be rate limited
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 429


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
