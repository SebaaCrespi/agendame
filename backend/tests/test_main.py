"""Tests for main FastAPI application."""

import pytest
from httpx import AsyncClient


class TestHealthCheck:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test GET /health returns 200 with status ok."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"


class TestCORS:
    """Test CORS configuration."""

    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client: AsyncClient):
        """Test CORS headers are present."""
        response = await async_client.options(
            "/api/v1/auth/register",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Should have CORS headers
        assert response.status_code in (200, 204)

    @pytest.mark.asyncio
    async def test_cors_allowed_origin(self, async_client: AsyncClient):
        """Test allowed origin gets CORS headers."""
        response = await async_client.post(
            "/api/v1/auth/register",
            headers={"Origin": "http://localhost:5173"},
            json={
                "email": "cors@test.com",
                "password": "ValidPass123",
                "nombre": "CORS Test",
                "rol": "CLIENTE",
            },
        )
        assert response.status_code == 201
        assert "access-control-allow-origin" in response.headers


class TestDocs:
    """Test API documentation endpoints."""

    @pytest.mark.asyncio
    async def test_docs_endpoint(self, async_client: AsyncClient):
        """Test /docs endpoint is accessible."""
        response = await async_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_openapi_json(self, async_client: AsyncClient):
        """Test /openapi.json endpoint is accessible."""
        response = await async_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Agendame API"

    @pytest.mark.asyncio
    async def test_redoc_endpoint(self, async_client: AsyncClient):
        """Test /redoc endpoint is accessible."""
        response = await async_client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestRouterMounting:
    """Test API routers are properly mounted."""

    @pytest.mark.asyncio
    async def test_auth_router_mounted(self, async_client: AsyncClient):
        """Test auth router is mounted at /api/v1/auth."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "router@test.com",
                "password": "password123",
                "nombre": "Router Test",
                "rol": "CLIENTE",
            },
        )
        # Should not be 404 (route exists)
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_unknown_route_returns_404(self, async_client: AsyncClient):
        """Test unknown route returns 404."""
        response = await async_client.get("/api/v1/unknown")
        assert response.status_code == 404


class TestExceptionHandling:
    """Test global exception handlers."""

    @pytest.mark.asyncio
    async def test_422_format(self, async_client: AsyncClient):
        """Test validation errors use RFC 7807 format."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid",
                "password": "short",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["type"] == "https://tools.ietf.org/html/rfc7231#section-6.5.1"
        assert data["title"] == "Validation Error"
        assert data["status"] == 422
        assert "errors" in data.get("extra", {})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
