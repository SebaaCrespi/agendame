"""CU-10: la baja de un profesional aplica la misma regla por PUT y por DELETE."""

from datetime import UTC, datetime

import pytest

from app.core import timeutils
from app.models.turno import TurnoEstado

ADMIN = "/api/v1/admin/profesionales"
PUBLICO = "/api/v1/profesionales"

# 15:00 UTC = 12:00 en Buenos Aires del 09/11/2026
AHORA = datetime(2026, 11, 9, 15, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def reloj(monkeypatch):
    monkeypatch.setattr(timeutils, "_utcnow", lambda: AHORA)


@pytest.fixture
def turno(make_turno, sample_cliente, sample_profesional, sample_servicio):
    async def crear(inicio: datetime, estado: TurnoEstado = TurnoEstado.CONFIRMADO):
        return await make_turno(sample_cliente, sample_profesional, sample_servicio, inicio=inicio, estado=estado)

    return crear


class TestBajaPorEdicion:
    async def test_con_turno_manana_409(self, async_client, admin_headers, db_session, sample_profesional, turno):
        await turno(datetime(2026, 11, 10, 10, 0, tzinfo=UTC))
        prof_id = sample_profesional.id
        response = await async_client.put(f"{ADMIN}/{prof_id}", json={"activo": False}, headers=admin_headers)
        assert response.status_code == 409
        assert "1 turno pendiente" in response.json()["detail"]

        # La sesión de tests es compartida: recargar antes de mirar el estado
        await db_session.refresh(sample_profesional)
        assert sample_profesional.activo is True

    async def test_con_turnos_ya_terminados_hoy(self, async_client, admin_headers, sample_profesional, turno):
        await turno(datetime(2026, 11, 9, 9, 0, tzinfo=UTC))  # 09:00-09:30, ya terminó
        response = await async_client.put(
            f"{ADMIN}/{sample_profesional.id}", json={"activo": False}, headers=admin_headers
        )
        assert response.status_code == 200, response.text
        assert response.json()["activo"] is False

    async def test_cancelados_no_impiden(self, async_client, admin_headers, sample_profesional, turno):
        await turno(datetime(2026, 11, 10, 10, 0, tzinfo=UTC), TurnoEstado.CANCELADO_CLIENTE)
        response = await async_client.put(
            f"{ADMIN}/{sample_profesional.id}", json={"activo": False}, headers=admin_headers
        )
        assert response.status_code == 200

    async def test_editar_otros_campos_con_turnos(self, async_client, admin_headers, sample_profesional, turno):
        await turno(datetime(2026, 11, 10, 10, 0, tzinfo=UTC))
        response = await async_client.put(
            f"{ADMIN}/{sample_profesional.id}", json={"telefono": "1122334455"}, headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["telefono"] == "1122334455"


class TestBajaPorDelete:
    async def test_turno_en_curso_409(self, async_client, admin_headers, sample_profesional, turno):
        await turno(datetime(2026, 11, 9, 11, 45, tzinfo=UTC), TurnoEstado.EN_CURSO)  # termina 12:15
        response = await async_client.delete(f"{ADMIN}/{sample_profesional.id}", headers=admin_headers)
        assert response.status_code == 409

    async def test_sin_turnos_204(self, async_client, admin_headers, sample_profesional):
        response = await async_client.delete(f"{ADMIN}/{sample_profesional.id}", headers=admin_headers)
        assert response.status_code == 204


class TestReactivar:
    async def test_vuelve_al_listado_publico(self, async_client, admin_headers, auth_headers, sample_profesional):
        await async_client.delete(f"{ADMIN}/{sample_profesional.id}", headers=admin_headers)
        response = await async_client.put(
            f"{ADMIN}/{sample_profesional.id}", json={"activo": True}, headers=admin_headers
        )
        assert response.status_code == 200
        publicos = await async_client.get(PUBLICO, headers=auth_headers)
        assert sample_profesional.id in [p["id"] for p in publicos.json()["items"]]
