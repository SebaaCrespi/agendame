"""Tests for business-time helpers."""

from datetime import UTC, datetime

import pytest

from app.core import timeutils


def test_ahora_negocio_convierte_a_hora_local(monkeypatch: pytest.MonkeyPatch):
    # 00:30 UTC del 3/11 = 21:30 del 2/11 en Buenos Aires (UTC-3)
    monkeypatch.setattr(timeutils, "_utcnow", lambda: datetime(2026, 11, 3, 0, 30, tzinfo=UTC))
    assert timeutils.ahora_negocio() == datetime(2026, 11, 2, 21, 30, tzinfo=UTC)


def test_ahora_negocio_respeta_configuracion(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(timeutils, "_utcnow", lambda: datetime(2026, 11, 3, 12, 0, tzinfo=UTC))
    monkeypatch.setattr(timeutils.settings, "BUSINESS_TIMEZONE", "UTC")
    assert timeutils.ahora_negocio() == datetime(2026, 11, 3, 12, 0, tzinfo=UTC)
