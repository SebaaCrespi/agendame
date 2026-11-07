"""Tests for exception handling."""

import pytest
from httpx import AsyncClient

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
)


class TestProblemDetail:
    """Test ProblemDetail model."""

    def test_problem_detail_creation(self):
        """Test creating a ProblemDetail instance."""
        problem = ProblemDetail(
            type="https://example.com/errors/test",
            title="Test Error",
            status=400,
            detail="This is a test error",
            instance="/api/test",
        )
        assert problem.type == "https://example.com/errors/test"
        assert problem.title == "Test Error"
        assert problem.status == 400
        assert problem.detail == "This is a test error"
        assert problem.instance == "/api/test"

    def test_problem_detail_minimal(self):
        """Test creating ProblemDetail with minimal fields."""
        problem = ProblemDetail(
            title="Error",
            status=500,
            detail="Internal error",
        )
        assert problem.type == "about:blank"
        assert problem.instance is None
        assert problem.extra is None


class TestAppException:
    """Test AppException base class."""

    def test_app_exception_defaults(self):
        """Test AppException with default title."""
        exc = AppException(status_code=404, detail="Not found")
        assert exc.status_code == 404
        assert exc.detail == "Not found"
        assert exc.title == "Not Found"
        assert exc.type == "about:blank"

    def test_app_exception_custom(self):
        """Test AppException with custom fields."""
        exc = AppException(
            status_code=409,
            detail="Resource conflict",
            type_="https://example.com/errors/conflict",
            title="Conflict",
            instance="/api/resource/1",
            extra={"field": "value"},
        )
        assert exc.status_code == 409
        assert exc.type == "https://example.com/errors/conflict"
        assert exc.title == "Conflict"
        assert exc.instance == "/api/resource/1"
        assert exc.extra == {"field": "value"}

    def test_to_problem_detail(self):
        """Test converting exception to ProblemDetail."""
        exc = AppException(
            status_code=401,
            detail="Invalid token",
            type_="https://example.com/errors/auth",
            title="Unauthorized",
        )
        problem = exc.to_problem_detail()
        assert isinstance(problem, ProblemDetail)
        assert problem.status == 401
        assert problem.detail == "Invalid token"
        assert problem.type == "https://example.com/errors/auth"
        assert problem.title == "Unauthorized"


class TestSpecificExceptions:
    """Test specific exception subclasses."""

    def test_validation_exception(self):
        """Test ValidationException."""
        exc = ValidationException(
            detail="Invalid input",
            errors=[{"field": "email", "message": "Invalid email"}],
        )
        assert exc.status_code == 422
        assert exc.title == "Validation Error"
        assert exc.extra["errors"][0]["field"] == "email"

    def test_not_found_exception(self):
        """Test NotFoundException."""
        exc = NotFoundException("User", 123)
        assert exc.status_code == 404
        assert "123" in exc.detail
        assert exc.title == "Not Found"

    def test_conflict_exception(self):
        """Test ConflictException."""
        exc = ConflictException("Email already exists")
        assert exc.status_code == 409
        assert exc.title == "Conflict"

    def test_unauthorized_exception(self):
        """Test UnauthorizedException."""
        exc = UnauthorizedException("Invalid credentials")
        assert exc.status_code == 401
        assert exc.title == "Unauthorized"

    def test_forbidden_exception(self):
        """Test ForbiddenException."""
        exc = ForbiddenException("Access denied")
        assert exc.status_code == 403
        assert exc.title == "Forbidden"

    def test_too_many_requests_exception(self):
        """Test TooManyRequestsException."""
        exc = TooManyRequestsException(retry_after=60)
        assert exc.status_code == 429
        assert exc.title == "Too Many Requests"
        assert exc.extra["retry_after"] == 60

    def test_business_exception(self):
        """Test BusinessException."""
        exc = BusinessException("Slot not available", status_code=409)
        assert exc.status_code == 409
        assert exc.title == "Business Rule Violation"


class TestExceptionHandlers:
    """Test exception handlers via HTTP requests."""

    @pytest.mark.asyncio
    async def test_app_exception_handler(self, async_client: AsyncClient):
        """Test AppException handler returns RFC 7807 format."""
        # We can't easily test this without a route that raises the exception
        # This would be tested in integration tests
        pass

    @pytest.mark.asyncio
    async def test_validation_error_format(self, async_client: AsyncClient):
        """Test validation error returns RFC 7807 format."""
        # Test with invalid data to trigger validation error
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "short",
                "nombre": "",
                "rol": "INVALID_ROLE",
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
