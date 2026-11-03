from functools import lru_cache

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

    # Groq API (Chatbot IA)
    GROQ_API_KEY: str = Field(default="", description="Groq API key for LLM")
    CHAT_MODEL: str = Field(
        default="llama-3.3-70b-versatile", description="Groq chat model name"
    )

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
