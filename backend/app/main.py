"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.deps import limiter
from app.api.v1 import (
    auth_router,
    chat_router,
    chatbot_router,
    profesionales_admin_router,
    profesionales_me_router,
    profesionales_public_router,
    turnos_admin_router,
    turnos_router,
)
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Agendame API",
        description="Sistema de gestión de turnos multi-prestador",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Rate limiting (slowapi needs the limiter on app.state and a 429 handler)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # Include routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(profesionales_admin_router, prefix="/api/v1")
    app.include_router(profesionales_me_router, prefix="/api/v1")
    app.include_router(profesionales_public_router, prefix="/api/v1")
    app.include_router(turnos_router, prefix="/api/v1")
    app.include_router(turnos_admin_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(chatbot_router, prefix="/api/v1")

    # Health check endpoint
    @app.get(
        "/health",
        tags=["Health"],
        summary="Health check",
        description="Verifica que el servicio está funcionando correctamente.",
    )
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "version": "1.0.0"}

    return app


app = create_app()
