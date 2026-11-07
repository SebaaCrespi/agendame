from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./agendame.db",
        description="SQLAlchemy async database URL",
    )

    # JWT Security
    JWT_SECRET_KEY: str = Field(
        description="Secret key for signing JWT tokens (min 32 chars)",
        min_length=32,
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440, description="Access token expiration in minutes (24h)"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration in days"
    )

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:5173"],
        description="Allowed CORS origins",
    )

    # Chatbot IA (CU-05/06): proveedor y modelo configurables
    CHAT_PROVIDER: Literal["groq", "nvidia", "ollama"] = Field(
        default="groq", description="Proveedor del modelo de lenguaje"
    )
    CHAT_MODEL: str = Field(
        default="openai/gpt-oss-120b", description="Modelo del proveedor elegido"
    )
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    NVIDIA_API_KEY: str = Field(default="", description="NVIDIA API key (build.nvidia.com)")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="URL de Ollama local")
    CHAT_TEMPERATURE: float = Field(default=0.1, ge=0, le=1)
    CHAT_TIMEOUT_S: float = Field(default=20, gt=0, description="Timeout por llamada al modelo")
    CHAT_MAX_HISTORY: int = Field(default=10, ge=2, le=50, description="Mensajes recordados por conversación")
    CHAT_SESSION_TTL: int = Field(default=3600, ge=60, description="Segundos sin uso hasta que vence la conversación")

    # Internal API Key (for chatbot service)
    INTERNAL_API_KEY: str = Field(
        default="dev-internal-key-change-in-production",
        description="API key for internal services (chatbot)",
    )

    # Zona horaria del negocio: las horas de turnos, grillas y excepciones son hora local
    BUSINESS_TIMEZONE: str = Field(
        default="America/Argentina/Buenos_Aires",
        description="IANA timezone del negocio",
    )

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(
        default=5, description="Max requests per window for rate limiting"
    )
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=60, description="Rate limit window in seconds"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
