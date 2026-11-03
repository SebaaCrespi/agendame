"""API v1 module exports."""

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.profesionales_admin import router as profesionales_admin_router
from app.api.v1.profesionales_me import router as profesionales_me_router
from app.api.v1.profesionales_public import router as profesionales_public_router
from app.api.v1.turnos import router as turnos_router
from app.api.v1.turnos_admin import router as turnos_admin_router

__all__ = [
    "auth_router",
    "chat_router",
    "profesionales_admin_router",
    "profesionales_me_router",
    "profesionales_public_router",
    "turnos_admin_router",
    "turnos_router",
]
