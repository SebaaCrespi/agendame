"""Schemas del chatbot (CU-05/06)."""

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRequest(BaseModel):
    """Mensaje del usuario al asistente."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"mensaje": "¿Qué horarios tiene Juan mañana para un corte?", "session_id": None}}
    )

    mensaje: str = Field(min_length=1, max_length=1000, description="Texto del usuario")
    session_id: str | None = Field(default=None, max_length=64, description="Conversación a continuar")


class ChatMessageResponse(BaseModel):
    """Respuesta del asistente."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "respuesta": "Juan tiene libre mañana a las 10:00, 10:30 y 15:00. ¿Te reservo alguno?",
                "session_id": "3f2b9c1e-…",
                "acciones": [],
            }
        }
    )

    respuesta: str
    session_id: str
    acciones: list[str] = Field(default_factory=list, description="Cambios hechos: turno_reservado, turno_cancelado")
