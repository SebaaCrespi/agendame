"""Chatbot: endpoint del asistente (CU-05/06) y endpoint interno de reserva."""

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from langchain_core.language_models.chat_models import BaseChatModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional, limiter
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.schemas.turno import ChatbotReservarRequest, ChatbotReservarResponse
from app.services.chat_llm import ChatNoConfiguradoError, crear_llm
from app.services.chatbot_service import ChatbotService, ProveedorChatError
from app.services.turno_service import TurnoService

router = APIRouter(prefix="/internal/turnos", tags=["Interno - Chatbot"])
chat_router = APIRouter(prefix="/chat", tags=["Chatbot"])

NO_DISPONIBLE = "El asistente no está disponible ahora. Podés reservar desde «Reservar turno»."

_llm_cache: dict[tuple[str, str], BaseChatModel] = {}


def get_chat_llm() -> BaseChatModel:
    """Modelo del proveedor configurado (se reutiliza entre requests)."""
    clave = (settings.CHAT_PROVIDER, settings.CHAT_MODEL)
    if clave not in _llm_cache:
        try:
            _llm_cache[clave] = crear_llm(settings)
        except ChatNoConfiguradoError:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=NO_DISPONIBLE) from None
    return _llm_cache[clave]


@chat_router.post(
    "/message",
    response_model=ChatMessageResponse,
    summary="Enviar mensaje al asistente",
    description="Conversa con el asistente de turnos. Sin sesión solo consulta horarios; "
                "con sesión de cliente también reserva, lista y cancela sus turnos. Límite: 20 mensajes por minuto.",
)
@limiter.limit("20/minute")
async def enviar_mensaje(
    request: Request,
    data: ChatMessageRequest,
    session: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    llm: BaseChatModel = Depends(get_chat_llm),
) -> ChatMessageResponse:
    """Mensaje al asistente (CU-05/06)."""
    cliente_id: int | None = None
    if user is not None and user.rol == UserRole.CLIENTE:
        cliente = await TurnoService(session)._get_cliente_by_user_id(user.id)
        cliente_id = cliente.id if cliente else None

    try:
        return await ChatbotService(session, llm).responder(
            data.mensaje, data.session_id, user.id if user else None, cliente_id
        )
    except ProveedorChatError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=NO_DISPONIBLE) from None


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
