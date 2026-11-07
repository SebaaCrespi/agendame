"""CU-09: historial de turnos por momento y por varios estados (cliente y proveedor)."""

from datetime import UTC, datetime

import pytest

from app.core import timeutils
from app.models.turno import TurnoEstado

MIS_TURNOS = "/api/v1/turnos/mis-turnos"
PROF_TURNOS = "/api/v1/profesionales/me/turnos"


def _hora(dia: int, hora: int, minuto: int = 0) -> datetime:
    """Hora del negocio (etiquetada UTC) del día `dia` de noviembre de 2026."""
    return datetime(2026, 11, dia, hora, minuto, tzinfo=UTC)


@pytest.fixture
def reloj(monkeypatch):
    # 15:00 UTC = 12:00 en Buenos Aires del 10/11/2026
    monkeypatch.setattr(timeutils, "_utcnow", lambda: datetime(2026, 11, 10, 15, 0, tzinfo=UTC))


@pytest.fixture
async def turnos(reloj, make_turno, sample_cliente, sample_profesional, sample_servicio):
    """Turnos de 30 min: hace 3 días, ayer, en curso, hoy más tarde y mañana."""

    async def crear(inicio: datetime, estado: TurnoEstado = TurnoEstado.CONFIRMADO):
        return await make_turno(sample_cliente, sample_profesional, sample_servicio, inicio=inicio, estado=estado)

    return {
        "hace_3_dias": await crear(_hora(7, 10), TurnoEstado.FINALIZADO),
        "ayer": await crear(_hora(9, 10), TurnoEstado.CANCELADO_CLIENTE),
        "en_curso": await crear(_hora(10, 11, 50), TurnoEstado.EN_CURSO),
        "hoy": await crear(_hora(10, 16)),
        "manana": await crear(_hora(11, 10), TurnoEstado.CANCELADO_PROFESIONAL),
    }


def _ids(response) -> list[int]:
    assert response.status_code == 200, response.text
    return [t["id"] for t in response.json()["items"]]


class TestMomentoCliente:
    async def test_proximos_del_mas_cercano_al_mas_lejano(self, async_client, auth_headers, turnos):
        response = await async_client.get(MIS_TURNOS, params={"momento": "proximos"}, headers=auth_headers)
        assert _ids(response) == [turnos["en_curso"].id, turnos["hoy"].id, turnos["manana"].id]

    async def test_pasados_del_mas_reciente_al_mas_viejo(self, async_client, auth_headers, turnos):
        response = await async_client.get(MIS_TURNOS, params={"momento": "pasados"}, headers=auth_headers)
        assert _ids(response) == [turnos["ayer"].id, turnos["hace_3_dias"].id]

    async def test_sin_momento_conserva_orden_descendente(self, async_client, auth_headers, turnos):
        response = await async_client.get(MIS_TURNOS, headers=auth_headers)
        assert _ids(response)[0] == turnos["manana"].id
        assert len(_ids(response)) == 5

    async def test_momento_invalido_422(self, async_client, auth_headers):
        response = await async_client.get(MIS_TURNOS, params={"momento": "ayer"}, headers=auth_headers)
        assert response.status_code == 422


class TestVariosEstados:
    async def test_cancelados_por_cualquiera(self, async_client, auth_headers, turnos):
        response = await async_client.get(
            MIS_TURNOS,
            params=[("estado", "CANCELADO_CLIENTE"), ("estado", "CANCELADO_PROFESIONAL")],
            headers=auth_headers,
        )
        assert set(_ids(response)) == {turnos["ayer"].id, turnos["manana"].id}
        assert response.json()["total"] == 2

    async def test_un_solo_estado_sigue_funcionando(self, async_client, auth_headers, turnos):
        response = await async_client.get(MIS_TURNOS, params={"estado": "FINALIZADO"}, headers=auth_headers)
        assert _ids(response) == [turnos["hace_3_dias"].id]

    async def test_estado_inexistente_422(self, async_client, auth_headers):
        response = await async_client.get(MIS_TURNOS, params={"estado": "BORRADO"}, headers=auth_headers)
        assert response.status_code == 422

    async def test_estados_y_momento_combinados_con_paginacion(self, async_client, auth_headers, turnos):
        response = await async_client.get(
            MIS_TURNOS,
            params=[("estado", "CONFIRMADO"), ("estado", "EN_CURSO"), ("momento", "proximos"), ("size", 1)],
            headers=auth_headers,
        )
        body = response.json()
        assert _ids(response) == [turnos["en_curso"].id]
        assert body["total"] == 2
        assert body["pages"] == 2


class TestMomentoProveedor:
    async def test_pasados(self, async_client, proveedor_headers, turnos):
        response = await async_client.get(PROF_TURNOS, params={"momento": "pasados"}, headers=proveedor_headers)
        assert _ids(response) == [turnos["ayer"].id, turnos["hace_3_dias"].id]

    async def test_sin_momento_cronologico_para_la_grilla(self, async_client, proveedor_headers, turnos):
        response = await async_client.get(PROF_TURNOS, headers=proveedor_headers)
        assert _ids(response)[0] == turnos["hace_3_dias"].id

    async def test_varios_estados_y_rango(self, async_client, proveedor_headers, turnos):
        response = await async_client.get(
            PROF_TURNOS,
            params=[
                ("estado", "FINALIZADO"),
                ("estado", "CONFIRMADO"),
                ("desde", "2026-11-01"),
                ("hasta", "2026-11-30"),
            ],
            headers=proveedor_headers,
        )
        assert _ids(response) == [turnos["hace_3_dias"].id, turnos["hoy"].id]
