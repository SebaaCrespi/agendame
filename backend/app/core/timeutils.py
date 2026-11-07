"""Hora del negocio.

Convención del sistema: las fechas/horas de turnos, grillas y excepciones son la
hora de reloj del negocio, guardadas con etiqueta UTC
(`datetime.combine(fecha, hora).replace(tzinfo=UTC)`). Para comparar contra
"ahora" hay que usar la misma convención, no el UTC real.

Los timestamps de auditoría (created_at, confirmado_en, ...) siguen en UTC real.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.core.config import settings


def _utcnow() -> datetime:
    """Real UTC now (separate function so tests can patch the clock)."""
    return datetime.now(UTC)


def ahora_negocio() -> datetime:
    """Hora de reloj actual del negocio, etiquetada como UTC."""
    local = _utcnow().astimezone(ZoneInfo(settings.BUSINESS_TIMEZONE))
    return local.replace(tzinfo=UTC)
