"""Concurrency: two simultaneous requests for the same slot -> one 201, one 409."""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.models.turno import Turno
from tests.conftest import headers_for, proximo_dia_habil


@pytest.mark.slow
async def test_dos_reservas_simultaneas_mismo_slot(
    isolated_app, session_factory, test_user, sample_profesional, sample_servicio
):
    body = {
        "profesional_id": sample_profesional.id,
        "servicio_id": sample_servicio.id,
        "fecha": proximo_dia_habil(1).isoformat(),
        "hora_inicio": "09:00",
    }
    headers = headers_for(test_user)

    async with AsyncClient(transport=ASGITransport(app=isolated_app), base_url="http://test") as client:
        responses = await asyncio.gather(
            client.post("/api/v1/turnos", json=body, headers=headers),
            client.post("/api/v1/turnos", json=body, headers=headers),
        )

    assert sorted(r.status_code for r in responses) == [201, 409]

    async with session_factory() as session:
        total = await session.scalar(select(func.count()).select_from(Turno))
    assert total == 1
