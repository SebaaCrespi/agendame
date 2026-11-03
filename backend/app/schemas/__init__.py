"""Schemas module exports."""

from app.schemas.auth import (
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from app.schemas.pagination import (
    FilterParams,
    PageParams,
    PageResponse,
    create_page_response,
)
from app.schemas.profesional import (
    DisponibilidadCreate,
    DisponibilidadResponse,
    DisponibilidadUpdate,
    ExcepcionCreate,
    ExcepcionResponse,
    ExcepcionUpdate,
    GrillaDisponibilidadResponse,
    MiPerfilResponse,
    ProfesionalCreate,
    ProfesionalListResponse,
    ProfesionalResponse,
    ProfesionalUpdate,
    ServicioCreate,
    ServicioResponse,
    ServicioUpdate,
    SlotResponse,
    SlotsListResponse,
)
from app.schemas.turno import (
    ChatbotReservarRequest,
    ChatbotReservarResponse,
    ProfesionalConSlotsResponse,
    SlotDisponibleResponse,
    TurnoCancelar,
    TurnoCreate,
    TurnoEstadoUpdate,
    TurnoFiltros,
    TurnoListResponse,
    TurnoNotasUpdate,
    TurnoReasignar,
    TurnoResponse,
)

__all__ = [
    # Auth
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "TokenRefresh",
    "UserResponse",
    "UserUpdate",
    # Pagination
    "PageParams",
    "PageResponse",
    "FilterParams",
    "create_page_response",
    # Profesional
    "ProfesionalCreate",
    "ProfesionalUpdate",
    "ProfesionalResponse",
    "ProfesionalListResponse",
    # Servicio
    "ServicioCreate",
    "ServicioUpdate",
    "ServicioResponse",
    # Disponibilidad
    "DisponibilidadCreate",
    "DisponibilidadUpdate",
    "DisponibilidadResponse",
    "GrillaDisponibilidadResponse",
    # Excepcion
    "ExcepcionCreate",
    "ExcepcionUpdate",
    "ExcepcionResponse",
    # Slots
    "SlotResponse",
    "SlotsListResponse",
    # Perfil completo
    "MiPerfilResponse",
    # Turno
    "TurnoCreate",
    "TurnoResponse",
    "TurnoListResponse",
    "TurnoEstadoUpdate",
    "TurnoReasignar",
    "TurnoCancelar",
    "TurnoNotasUpdate",
    "TurnoFiltros",
    # Chatbot (Internal)
    "ChatbotReservarRequest",
    "ChatbotReservarResponse",
    # Disponibilidad (Cliente)
    "SlotDisponibleResponse",
    "ProfesionalConSlotsResponse",
]
