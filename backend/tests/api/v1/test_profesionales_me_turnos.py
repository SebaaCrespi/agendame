"""Integration tests for Profesional turnos endpoints (/profesionales/me/turnos)."""

from app.models.turno import TurnoEstado
from tests.conftest import headers_for, proximo_dia_habil

BASE = "/api/v1/profesionales/me/turnos"


class TestListar:
    async def test_lista_mis_turnos(self, async_client, proveedor_headers, sample_turno):
        response = await async_client.get(BASE, headers=proveedor_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == sample_turno.id

    async def test_filtro_estado(self, async_client, proveedor_headers, sample_turno):
        response = await async_client.get(BASE, params={"estado": "CONFIRMADO"}, headers=proveedor_headers)
        assert response.json()["total"] == 1
        response = await async_client.get(BASE, params={"estado": "FINALIZADO"}, headers=proveedor_headers)
        assert response.json()["total"] == 0

    async def test_filtro_fechas(self, async_client, proveedor_headers, sample_turno):
        dia = sample_turno.fecha_inicio.date()
        response = await async_client.get(
            BASE, params={"desde": dia.isoformat(), "hasta": dia.isoformat()}, headers=proveedor_headers
        )
        assert response.json()["total"] == 1

    async def test_no_ve_turnos_de_otro(self, async_client, sample_turno, make_profesional, db_session):
        from app.models.user import User

        otro = await make_profesional(nombre="Otro")
        user = await db_session.get(User, otro.user_id)
        response = await async_client.get(BASE, headers=headers_for(user))
        assert response.json()["total"] == 0

    async def test_proveedor_sin_perfil_404(self, async_client, profesional_headers):
        response = await async_client.get(BASE, headers=profesional_headers)
        assert response.status_code == 404

    async def test_cliente_403(self, async_client, auth_headers):
        response = await async_client.get(BASE, headers=auth_headers)
        assert response.status_code == 403


class TestDetalle:
    async def test_propio(self, async_client, proveedor_headers, sample_turno):
        response = await async_client.get(f"{BASE}/{sample_turno.id}", headers=proveedor_headers)
        assert response.status_code == 200

    async def test_inexistente_404(self, async_client, proveedor_headers):
        response = await async_client.get(f"{BASE}/9999", headers=proveedor_headers)
        assert response.status_code == 404


class TestAcciones:
    async def test_cambiar_estado(self, async_client, proveedor_headers, sample_turno):
        response = await async_client.put(
            f"{BASE}/{sample_turno.id}/estado", json={"nuevo_estado": "EN_CURSO"}, headers=proveedor_headers
        )
        assert response.status_code == 200, response.text
        assert response.json()["estado"] == TurnoEstado.EN_CURSO.value

    async def test_transicion_invalida_422(self, async_client, proveedor_headers, sample_turno):
        response = await async_client.put(
            f"{BASE}/{sample_turno.id}/estado", json={"nuevo_estado": "FINALIZADO"}, headers=proveedor_headers
        )
        assert response.status_code == 422

    async def test_reasignar(self, async_client, proveedor_headers, sample_turno):
        response = await async_client.put(
            f"{BASE}/{sample_turno.id}/reasignar",
            json={"nueva_fecha": proximo_dia_habil(5).isoformat(), "nueva_hora_inicio": "16:00", "motivo": "Agenda"},
            headers=proveedor_headers,
        )
        assert response.status_code == 200, response.text
        assert response.json()["fecha_inicio"].startswith(f"{proximo_dia_habil(5).isoformat()}T16:00")

    async def test_cancelar(self, async_client, proveedor_headers, sample_turno):
        response = await async_client.put(
            f"{BASE}/{sample_turno.id}/cancelar", json={"motivo": "Enfermo"}, headers=proveedor_headers
        )
        assert response.status_code == 200
        assert response.json()["estado"] == TurnoEstado.CANCELADO_PROFESIONAL.value

    async def test_notas(self, async_client, proveedor_headers, sample_turno):
        response = await async_client.put(
            f"{BASE}/{sample_turno.id}/notas",
            json={"notas_profesional": "Cliente frecuente"},
            headers=proveedor_headers,
        )
        assert response.status_code == 200
        assert response.json()["notas_profesional"] == "Cliente frecuente"
