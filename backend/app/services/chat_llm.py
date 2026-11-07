"""Modelo de lenguaje del chatbot según la configuración (CU-05/06)."""

from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import Settings


class ChatNoConfiguradoError(RuntimeError):
    """Falta la key o el proveedor no es válido: el chat no está disponible."""


def crear_llm(settings: Settings) -> BaseChatModel:
    """
    Arma el modelo del proveedor elegido en `CHAT_PROVIDER`.

    Los imports son perezosos: solo se carga el paquete del proveedor en uso.
    """
    proveedor = settings.CHAT_PROVIDER
    modelo, temperatura = settings.CHAT_MODEL, settings.CHAT_TEMPERATURE

    if proveedor == "groq":
        if not settings.GROQ_API_KEY.startswith("gsk_"):
            raise ChatNoConfiguradoError("Falta GROQ_API_KEY en el .env")
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=modelo,
            temperature=temperatura,
            api_key=settings.GROQ_API_KEY,  # type: ignore[arg-type]
            timeout=settings.CHAT_TIMEOUT_S,
            max_retries=1,
        )

    if proveedor == "nvidia":
        if not settings.NVIDIA_API_KEY:
            raise ChatNoConfiguradoError("Falta NVIDIA_API_KEY en el .env")
        from langchain_nvidia_ai_endpoints import ChatNVIDIA

        return ChatNVIDIA(model=modelo, temperature=temperatura, api_key=settings.NVIDIA_API_KEY)

    if proveedor == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=modelo, temperature=temperatura, base_url=settings.OLLAMA_BASE_URL)

    raise ChatNoConfiguradoError(f"CHAT_PROVIDER desconocido: {proveedor}")
