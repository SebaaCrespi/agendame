"""Integration tests for Cliente and Admin turnos endpoints."""

from datetime import timedelta

from httpx import AsyncClient

from app.models.turno import TurnoEstado
from tests.conftest import proximo_dia_habil

BASE = "/api/v1/turnos"


def _reserva(profesional_id: int, servicio_id: int, dias: int = 1, hora: str = "09:00") -> dict:
    return {
        "profesional_id": profesional_id,
        "servicio_id": servicio_id,
        "fecha": proximo_dia_habil(dias).isoformat(),
        "hora_inicio": hora,
    }


class TestDisponibilidad:
    async def test_requiere_auth(self, async_client: AsyncClient):
        dia = proximo_dia_habil(1).isoformat()
        response = await async_client.get(f"{BASE}/disponibilidad", params={"desde": dia, "hasta": dia})
        assert response.status_code == 401

    async def test_por_profesional(self, async_client, auth_headers, sample_profesional, sample_servicio):
        dia = proximo_dia_habil(1).isoformat()
        response = await async_client.get(
            f"{BASE}/disponibilidad",
            params={"desde": dia, "hasta": dia, "profesional_id": sample_profesional.id},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["profesionales"][0]["profesional_id"] == sample_profesional.id
        assert len(data["profesionales"][0]["slots_por_fecha"][dia]) == 18

    async def test_faltan_fechas_422(self, async_client, auth_headers):
        response = await async_client.get(f"{BASE}/disponibilidad", headers=auth_headers)
        assert response.status_code == 422

    async def test_proveedor_no_puede_403(self, async_client, proveedor_headers):
        dia = proximo_dia_habil(1).isoformat()
        response = await async_client.get(
            f"{BASE}/disponibilidad", params={"desde": dia, "hasta": dia}, headers=proveedor_headers
        )
        assert response.status_code == 403


class TestCrearReserva:
    async def test_exitosa(self, async_client, auth_headers, sample_cliente, sample_profesional, sample_servicio):
        response = await async_client.post(
            BASE, json=_reserva(sample_profesional.id, sample_servicio.id), headers=auth_headers
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["estado"] == TurnoEstado.CONFIRMADO.value
        assert data["cliente_id"] == sample_cliente.id
        assert data["creado_por"] == "cliente"

    async def test_slot_ocupado_409(self, async_client, auth_headers, sample_profesional, sample_servicio):
        body = _reserva(sample_profesional.id, sample_servicio.id)
        first = await async_client.post(BASE, json=body, headers=auth_headers)
        assert first.status_code == 201
        second = await async_client.post(BASE, json=body, headers=auth_headers)
        assert second.status_code == 409

    async def test_fecha_pasada_422(self, async_client, auth_headers, sample_profesional, sample_servicio):
        response = await async_client.post(
            BASE, json=_reserva(sample_profesional.id, sample_servicio.id, dias=-1), headers=auth_headers
        )
        assert response.status_code == 422

    async def test_servicio_inexistente_404(self, async_client, auth_headers, sample_profesional):
        response = await async_client.post(BASE, json=_reserva(sample_profesional.id, 9999), headers=auth_headers)
        assert response.status_code == 404

    async def test_registro_crea_perfil_cliente_y_puede_reservar(
        self, async_client, sample_profesional, sample_servicio
    ):
        reg = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "nuevo@test.com", "password": "Clave12345", "nombre": "Nuevo", "rol": "CLIENTE"},
        )
        assert reg.status_code == 201
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        response = await async_client.post(
            BASE, json=_reserva(sample_profesional.id, sample_servicio.id), headers=headers
        )
        assert response.status_code == 201, response.text


class TestMisTurnos:
    async def test_lista_solo_los_propios(
        self, async_client, auth_headers, sample_turno, make_turno, sample_profesional, sample_servicio, db_session
    ):
        from app.repositories.user_repo import UserRepo
        from tests.conftest import unique_email

        otro_user = await UserRepo(db_session).create(unique_email("otro"), "Clave12345", "Otro")
        await db_session.commit()
        await db_session.refresh(otro_user, ["cliente"])
        await make_turno(
            otro_user.cliente,
            sample_profesional,
            sample_servicio,
            inicio=sample_turno.fecha_inicio + timedelta(hours=2),
        )

        response = await async_client.get(f"{BASE}/mis-turnos", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == sample_turno.id

    async def test_filtro_por_estado(self, async_client, auth_headers, sample_turno):
        response = await async_client.get(
            f"{BASE}/mis-turnos", params={"estado": "CANCELADO_CLIENTE"}, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0

    async def test_paginacion(self, async_client, auth_headers, sample_turno):
        response = await async_client.get(f"{BASE}/mis-turnos", params={"page": 1, "size": 10}, headers=auth_headers)
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 10
        assert data["pages"] == 1


class TestDetalleYCancelar:
    async def test_detalle_propio(self, async_client, auth_headers, sample_turno):
        response = await async_client.get(f"{BASE}/{sample_turno.id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == sample_turno.id

    async def test_detalle_inexistente_404(self, async_client, auth_headers, sample_cliente):
        response = await async_client.get(f"{BASE}/9999", headers=auth_headers)
        assert response.status_code == 404

    async def test_cancelar(self, async_client, auth_headers, sample_turno):
        response = await async_client.put(
            f"{BASE}/{sample_turno.id}/cancelar", json={"motivo": "Viaje"}, headers=auth_headers
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["estado"] == TurnoEstado.CANCELADO_CLIENTE.value
        assert data["motivo_cancelacion"] == "Viaje"

    async def test_cancelar_sin_motivo_422(self, async_client, auth_headers, sample_turno):
        response = await async_client.put(f"{BASE}/{sample_turno.id}/cancelar", json={}, headers=auth_headers)
        assert response.status_code == 422

    async def test_slot_queda_libre_tras_cancelar(
        self, async_client, auth_headers, sample_turno, sample_profesional, sample_servicio
    ):
        await async_client.put(f"{BASE}/{sample_turno.id}/cancelar", json={"motivo": "x"}, headers=auth_headers)
        body = {
            "profesional_id": sample_profesional.id,
            "servicio_id": sample_servicio.id,
            "fecha": sample_turno.fecha_inicio.date().isoformat(),
            "hora_inicio": "10:00",
        }
        response = await async_client.post(BASE, json=body, headers=auth_headers)
        assert response.status_code == 201


class TestAdminTurnos:
    async def test_lista_todos(self, async_client, admin_headers, sample_turno):
        response = await async_client.get("/api/v1/admin/turnos", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1

    async def test_detalle(self, async_client, admin_headers, sample_turno):
        response = await async_client.get(f"/api/v1/admin/turnos/{sample_turno.id}", headers=admin_headers)
        assert response.status_code == 200

    async def test_cliente_no_puede_403(self, async_client, auth_headers):
        response = await async_client.get("/api/v1/admin/turnos", headers=auth_headers)
        assert response.status_code == 403


class TestDisponibilidadConServicio:
    async def test_servicio_de_60_no_ofrece_17_30(
        self, async_client, auth_headers, sample_profesional, servicio_largo
    ):
        dia = proximo_dia_habil(2).isoformat()
        response = await async_client.get(
            f"{BASE}/disponibilidad",
            params={"desde": dia, "hasta": dia, "profesional_id": sample_profesional.id, "servicio_id": servicio_largo.id},
            headers=auth_headers,
        )
        assert response.status_code == 200
        inicios = [s["hora_inicio"] for s in response.json()["profesionales"][0]["slots_por_fecha"][dia]]
        assert inicios[-1] == "17:00:00"
        assert "17:30:00" not in inicios


class TestReservaFueraDeHorario:
    async def test_antes_de_abrir_422(self, async_client, auth_headers, sample_profesional, sample_servicio):
        response = await async_client.post(
            BASE, json=_reserva(sample_profesional.id, sample_servicio.id, hora="07:00"), headers=auth_headers
        )
        assert response.status_code == 422

    async def test_desalineado_422(self, async_client, auth_headers, sample_profesional, sample_servicio):
        response = await async_client.post(
            BASE, json=_reserva(sample_profesional.id, sample_servicio.id, hora="09:10"), headers=auth_headers
        )
        assert response.status_code == 422
