"""CU-05/06: el proveedor del modelo se elige por configuración."""

import pytest

from app.core.config import Settings
from app.services.chat_llm import ChatNoConfiguradoError, crear_llm


def _settings(**valores) -> Settings:
    base = {"JWT_SECRET_KEY": "x" * 32, "GROQ_API_KEY": "", "NVIDIA_API_KEY": ""}
    return Settings(**{**base, **valores})  # type: ignore[arg-type]


def test_groq():
    llm = crear_llm(_settings(CHAT_PROVIDER="groq", GROQ_API_KEY="gsk_" + "a" * 40, CHAT_MODEL="llama-3.3-70b-versatile"))
    assert type(llm).__name__ == "ChatGroq"


def test_groq_sin_key():
    with pytest.raises(ChatNoConfiguradoError, match="GROQ_API_KEY"):
        crear_llm(_settings(CHAT_PROVIDER="groq"))


def test_nvidia():
    llm = crear_llm(_settings(CHAT_PROVIDER="nvidia", NVIDIA_API_KEY="nvapi-test", CHAT_MODEL="openai/gpt-oss-20b"))
    assert type(llm).__name__ == "ChatNVIDIA"


def test_nvidia_sin_key():
    with pytest.raises(ChatNoConfiguradoError, match="NVIDIA_API_KEY"):
        crear_llm(_settings(CHAT_PROVIDER="nvidia"))


def test_ollama():
    llm = crear_llm(_settings(CHAT_PROVIDER="ollama", CHAT_MODEL="qwen2.5:7b"))
    assert type(llm).__name__ == "ChatOllama"


def test_proveedor_desconocido():
    with pytest.raises(Exception):
        _settings(CHAT_PROVIDER="openai")
