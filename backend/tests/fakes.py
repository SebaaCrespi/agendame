"""Modelo de lenguaje falso para testear el chatbot sin red."""

from collections.abc import Sequence
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


def llamada(herramienta: str, /, **args: Any) -> dict[str, Any]:
    """Un tool call como los que devuelve un modelo real."""
    return {"name": herramienta, "args": args, "id": f"call_{herramienta}_{len(args)}", "type": "tool_call"}


class FakeToolModel(BaseChatModel):
    """
    Devuelve, en orden, las respuestas guionadas (AIMessage, con o sin tool_calls).
    Registra los mensajes que recibió en cada llamada y las herramientas vinculadas.
    """

    respuestas: list[AIMessage]
    recibidos: list[list[BaseMessage]] = []
    herramientas: list[str] = []
    error: Exception | None = None

    @property
    def _llm_type(self) -> str:
        return "fake-tool-model"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "FakeToolModel":  # type: ignore[override]
        self.herramientas = [getattr(t, "name", str(t)) for t in tools]
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self.error is not None:
            raise self.error
        self.recibidos.append(list(messages))
        if not self.respuestas:
            raise AssertionError("El modelo falso se quedó sin respuestas guionadas")
        mensaje = self.respuestas.pop(0)
        return ChatResult(generations=[ChatGeneration(message=mensaje)])
