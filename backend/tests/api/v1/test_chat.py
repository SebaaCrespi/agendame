"""Integration tests for the internal chatbot endpoint (/internal/turnos/reservar).

The conversational chatbot (LangChain + Groq, CU-05/CU-06) is not implemented
yet; these tests only cover the internal booking API it will use.
"""

from tests.conftest import proximo_dia_habil

URL = "/api/v1/internal/turnos/reservar"


def _body(cliente_id: int, profesional_id: int, servicio_id: int, hora: str = "09:00") -> dict:
    return {
        "cliente_id": cliente_id,
        "profesional_id": profesional_id,
        "servicio_id": servicio_id,
        "fecha": proximo_dia_habil(1).isoformat(),
        "hora_inicio": hora,
    }


class TestChatbotReservar:
    async def test_exitoso(self, async_client, api_key_header, sample_cliente, sample_profesional, sample_servicio):
        response = await async_client.post(
            URL, json=_body(sample_cliente.id, sample_profesional.id, sample_servicio.id), headers=api_key_header
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["turno_id"] > 0
        assert data["profesional_nombre"] == "Juan Perez"
        assert data["servicio_nombre"] == "Corte"

    async def test_api_key_invalida_401(self, async_client):
        response = await async_client.post(URL, json=_body(1, 1, 1), headers={"X-Internal-API-Key": "mala"})
        assert response.status_code == 401

    async def test_api_key_faltante_422(self, async_client):
        response = await async_client.post(URL, json=_body(1, 1, 1))
        assert response.status_code == 422

    async def test_slot_ocupado_409(
        self, async_client, api_key_header, sample_cliente, sample_profesional, sample_servicio
    ):
        body = _body(sample_cliente.id, sample_profesional.id, sample_servicio.id)
        assert (await async_client.post(URL, json=body, headers=api_key_header)).status_code == 200
        assert (await async_client.post(URL, json=body, headers=api_key_header)).status_code == 409

    async def test_datos_incompletos_422(self, async_client, api_key_header):
        response = await async_client.post(URL, json={"cliente_id": 1}, headers=api_key_header)
        assert response.status_code == 422

    async def test_cliente_inexistente_404(self, async_client, api_key_header, sample_profesional, sample_servicio):
        response = await async_client.post(
            URL, json=_body(9999, sample_profesional.id, sample_servicio.id), headers=api_key_header
        )
        assert response.status_code == 404
