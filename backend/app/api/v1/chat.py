"""Internal API endpoints for Chatbot integration."""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.turno import ChatbotReservarRequest, ChatbotReservarResponse
from app.services.turno_service import TurnoService

router = APIRouter(prefix="/internal/turnos", tags=["Interno - Chatbot"])


async def require_internal_api_key(
    x_internal_api_key: str = Header(..., alias="X-Internal-API-Key"),
) -> None:
    """Validate internal API key for chatbot access."""
    if x_internal_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/reservar",
    response_model=ChatbotReservarResponse,
    summary="Crear turno desde chatbot",
    description="Endpoint interno para que el servicio de chatbot cree turnos. "
                "Requiere header X-Internal-API-Key. "
                "Valida igual que reserva manual: cliente existe, profesional activo, "
                "servicio del profesional, slot libre. Retorna datos para respuesta conversacional.",
    dependencies=[Depends(require_internal_api_key)],
)
async def reservar_desde_chatbot(
    data: ChatbotReservarRequest,
    session: AsyncSession = Depends(get_db),
) -> ChatbotReservarResponse:
    """Crear turno desde chatbot (interno)."""
    service = TurnoService(session)
    try:
        return await service.crear_turno_desde_chatbot(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
