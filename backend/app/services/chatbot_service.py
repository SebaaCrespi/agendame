"""
Chatbot de turnos (CU-05/06).

Bucle propio sobre `bind_tools`: el modelo pide herramientas, se ejecutan con las
validaciones de los servicios y se le devuelve el resultado hasta que responde.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.timeutils import ahora_negocio
from app.schemas.chat import ChatMessageResponse
from app.services.chat_tools import crear_herramientas, hoy_texto

logger = logging.getLogger(__name__)

MAX_VUELTAS = 5
SIN_RESOLVER = (
    "No pude resolverlo por acá. Podés reservar o cancelar desde «Reservar turno» y «Mis turnos»."
)

SYSTEM_PROMPT = """Sos "Agendame", el asistente de reservas de una peluquería. Hoy es {hoy}.

Podés: consultar horarios libres, reservar turnos y, si el cliente inició sesión, ver y cancelar sus próximos turnos.

Reglas:
- Usá SIEMPRE las herramientas para datos reales. Nunca inventes profesionales, servicios ni horarios.
- Para consultar horarios necesitás el id del profesional y del servicio: si no los tenés, buscalos con buscar_profesionales.
- Resolvé "hoy", "mañana", "el viernes", etc. a partir de la fecha de hoy y usá fechas AAAA-MM-DD en las herramientas.
- Si falta un dato, preguntá una sola cosa por vez.
- ANTES de reservar o cancelar, resumí lo que vas a hacer (profesional, servicio, día y hora) y esperá que el cliente confirme. Sin confirmación explícita no llames a reservar_turno ni a cancelar_turno.
- Si una herramienta devuelve "Error:", explicalo en palabras simples y ofrecé una alternativa (otros horarios, otro día).
- Respondé en español, breve y amable. Horas en formato HH:MM.
{sesion}"""

SESION_CLIENTE = "El usuario inició sesión como cliente: podés reservar, ver y cancelar SUS turnos."
SESION_ANONIMA = "El usuario NO inició sesión como cliente: solo podés consultar; para reservar, ver o cancelar pedile que inicie sesión."


class ProveedorChatError(RuntimeError):
    """El proveedor del modelo no respondió o devolvió error."""


@dataclass
class _Conversacion:
    user_id: int | None
    mensajes: list[BaseMessage] = field(default_factory=list)
    actualizado: float = field(default_factory=time.monotonic)


class ChatSessionStore:
    """Conversaciones en memoria (un solo proceso): últimos N mensajes, vencen tras TTL sin uso."""

    def __init__(self, max_mensajes: int, ttl_s: int):
        self.max_mensajes = max_mensajes
        self.ttl_s = ttl_s
        self._data: dict[str, _Conversacion] = {}
        self._lock = asyncio.Lock()

    def _purgar(self, ahora: float) -> None:
        vencidas = [k for k, c in self._data.items() if ahora - c.actualizado > self.ttl_s]
        for k in vencidas:
            del self._data[k]

    async def obtener(self, session_id: str | None, user_id: int | None) -> tuple[str, list[BaseMessage]]:
        """Historial de la conversación; si no existe o es de otro usuario, empieza una nueva."""
        async with self._lock:
            ahora = time.monotonic()
            self._purgar(ahora)
            conv = self._data.get(session_id) if session_id else None
            if conv is None or conv.user_id != user_id:
                session_id = str(uuid.uuid4())
                conv = _Conversacion(user_id=user_id)
                self._data[session_id] = conv
            conv.actualizado = ahora
            assert session_id is not None
            return session_id, list(conv.mensajes)

    async def guardar(self, session_id: str, nuevos: list[BaseMessage]) -> None:
        async with self._lock:
            conv = self._data.get(session_id)
            if conv is None:
                return
            conv.mensajes = (conv.mensajes + nuevos)[-self.max_mensajes :]
            conv.actualizado = time.monotonic()

    def limpiar(self) -> None:
        self._data.clear()


store = ChatSessionStore(settings.CHAT_MAX_HISTORY, settings.CHAT_SESSION_TTL)


class ChatbotService:
    """Responde un mensaje usando el modelo y las herramientas de la sesión."""

    def __init__(self, session: AsyncSession, llm: BaseChatModel, sesiones: ChatSessionStore = store):
        self.session = session
        self.llm = llm
        self.sesiones = sesiones

    async def responder(
        self, mensaje: str, session_id: str | None, user_id: int | None, cliente_id: int | None
    ) -> ChatMessageResponse:
        session_id, historial = await self.sesiones.obtener(session_id, user_id)
        acciones: list[str] = []
        herramientas = crear_herramientas(self.session, cliente_id, acciones)
        por_nombre = {t.name: t for t in herramientas}
        modelo = self.llm.bind_tools(herramientas)

        sistema = SystemMessage(
            SYSTEM_PROMPT.format(
                hoy=hoy_texto(ahora_negocio()),
                sesion=SESION_CLIENTE if cliente_id is not None else SESION_ANONIMA,
            )
        )
        humano = HumanMessage(mensaje.strip())
        mensajes: list[BaseMessage] = [sistema, *historial, humano]

        respuesta = SIN_RESOLVER
        for _ in range(MAX_VUELTAS):
            try:
                ai = await modelo.ainvoke(mensajes)
            except Exception as e:  # red, timeout, cupo, key inválida…
                logger.warning("chat: fallo del proveedor (%s)", type(e).__name__)
                raise ProveedorChatError(str(e)) from e
            assert isinstance(ai, AIMessage)
            mensajes.append(ai)
            if not ai.tool_calls:
                respuesta = str(ai.content).strip() or SIN_RESOLVER
                break
            for call in ai.tool_calls:
                herramienta = por_nombre.get(call["name"])
                logger.info("chat tool %s", call["name"])
                resultado = (
                    await herramienta.ainvoke(call["args"])
                    if herramienta
                    else f"Error: no existe la herramienta {call['name']}"
                )
                mensajes.append(ToolMessage(content=str(resultado), tool_call_id=call["id"] or call["name"]))

        # Solo se recuerda el intercambio visible (sin resultados de herramientas)
        await self.sesiones.guardar(session_id, [humano, AIMessage(respuesta)])
        return ChatMessageResponse(respuesta=respuesta, session_id=session_id, acciones=acciones)
