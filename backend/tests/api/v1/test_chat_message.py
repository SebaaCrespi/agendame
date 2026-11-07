"""CU-05/06: servicio del chatbot y POST /chat/message con un modelo falso (sin red)."""

from datetime import UTC, datetime

import pytest
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from app.api.v1 import chat as chat_api
from app.core import timeutils
from app.models.turno import Turno
from app.services import chatbot_service
from app.services.chatbot_service import MAX_VUELTAS, SIN_RESOLVER, ChatbotService, ChatSessionStore
from tests.fakes import FakeToolModel, llamada

URL = "/api/v1/chat/message"
AHORA = datetime(2026, 11, 9, 15, 0, tzinfo=UTC)  # lunes 12:00 en Buenos Aires


@pytest.fixture(autouse=True)
def reloj(monkeypatch):
    monkeypatch.setattr(timeutils, "_utcnow", lambda: AHORA)


@pytest.fixture(autouse=True)
def limpiar_conversaciones():
    chatbot_service.store.limpiar()
    chat_api._llm_cache.clear()
    yield
    chatbot_service.store.limpiar()
    chat_api._llm_cache.clear()


@pytest.fixture
def modelo(monkeypatch):
    """Instala un modelo falso como proveedor del endpoint."""

    def instalar(*respuestas: AIMessage, error: Exception | None = None) -> FakeToolModel:
        fake = FakeToolModel(respuestas=list(respuestas), recibidos=[], error=error)
        monkeypatch.setattr(chat_api, "crear_llm", lambda _s: fake)
        return fake

    return instalar


def _ai(texto: str = "", *calls) -> AIMessage:
    return AIMessage(content=texto, tool_calls=list(calls))


class TestServicio:
    async def test_respuesta_directa_con_fecha_en_el_prompt(self, db_session):
        fake = FakeToolModel(respuestas=[_ai("¡Hola! ¿En qué te ayudo?")], recibidos=[])
        r = await ChatbotService(db_session, fake, ChatSessionStore(10, 3600)).responder("hola", None, None, None)
        assert r.respuesta == "¡Hola! ¿En qué te ayudo?"
        sistema = fake.recibidos[0][0]
        assert isinstance(sistema, SystemMessage) and "lunes 2026-11-09" in str(sistema.content)
        assert "NO inició sesión" in str(sistema.content)
        assert set(fake.herramientas) == {"buscar_profesionales", "consultar_disponibilidad", "reservar_turno", "mis_turnos", "cancelar_turno"}

    async def test_dos_herramientas_encadenadas(self, db_session, sample_profesional, sample_servicio):
        fake = FakeToolModel(
            respuestas=[
                _ai("", llamada("buscar_profesionales", **{"nombre": "Juan"})),
                _ai("", llamada("consultar_disponibilidad", profesional_id=sample_profesional.id, servicio_id=sample_servicio.id, desde="2026-11-10")),
                _ai("Juan tiene libre mañana desde las 09:00."),
            ],
            recibidos=[],
        )
        r = await ChatbotService(db_session, fake, ChatSessionStore(10, 3600)).responder("horarios de Juan mañana", None, None, None)
        assert r.respuesta.startswith("Juan tiene libre")
        resultado = fake.recibidos[2][-1]
        assert isinstance(resultado, ToolMessage) and "09:00" in str(resultado.content)

    async def test_limite_de_vueltas(self, db_session):
        respuestas = [_ai("", llamada("mis_turnos")) for _ in range(MAX_VUELTAS)]
        fake = FakeToolModel(respuestas=respuestas, recibidos=[])
        r = await ChatbotService(db_session, fake, ChatSessionStore(10, 3600)).responder("x", None, None, None)
        assert r.respuesta == SIN_RESOLVER

    async def test_sin_tool_call_no_reserva(self, db_session, sample_cliente, sample_profesional, sample_servicio):
        fake = FakeToolModel(respuestas=[_ai("¿Confirmás corte con Juan mañana a las 10:00?")], recibidos=[])
        await ChatbotService(db_session, fake, ChatSessionStore(10, 3600)).responder(
            "quiero un corte con Juan mañana a las 10", None, 1, sample_cliente.id
        )
        from sqlalchemy import func, select

        assert (await db_session.scalar(select(func.count(Turno.id)))) == 0

    async def test_historial_recortado_y_sin_resultados_de_herramientas(self, db_session):
        store = ChatSessionStore(4, 3600)
        fake = FakeToolModel(respuestas=[_ai("", llamada("mis_turnos")), _ai("r1"), _ai("r2"), _ai("r3")], recibidos=[])
        service = ChatbotService(db_session, fake, store)
        sid = (await service.responder("m1", None, 7, None)).session_id
        await service.responder("m2", sid, 7, None)
        await service.responder("m3", sid, 7, None)
        _, historial = await store.obtener(sid, 7)
        assert [str(m.content) for m in historial] == ["m2", "r2", "m3", "r3"]

    async def test_conversacion_ajena_empieza_de_cero(self):
        store = ChatSessionStore(10, 3600)
        sid, _ = await store.obtener(None, 1)
        await store.guardar(sid, [AIMessage("secreto")])
        otro_sid, historial = await store.obtener(sid, 2)
        assert otro_sid != sid and historial == []

    async def test_vencimiento(self, monkeypatch):
        store = ChatSessionStore(10, 60)
        reloj_mono = [1000.0]
        monkeypatch.setattr(chatbot_service.time, "monotonic", lambda: reloj_mono[0])
        sid, _ = await store.obtener(None, 1)
        await store.guardar(sid, [AIMessage("hola")])
        reloj_mono[0] += 61
        nuevo, historial = await store.obtener(sid, 1)
        assert nuevo != sid and historial == []


class TestEndpoint:
    async def test_cliente_reserva_a_su_nombre(
        self, async_client, auth_headers, modelo, db_session, sample_cliente, sample_profesional, sample_servicio
    ):
        modelo(
            _ai("", llamada("reservar_turno", profesional_id=sample_profesional.id, servicio_id=sample_servicio.id, fecha="2026-11-10", hora="10:00")),
            _ai("¡Listo! Corte con Juan mañana a las 10:00."),
        )
        response = await async_client.post(URL, json={"mensaje": "sí, confirmo"}, headers=auth_headers)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["acciones"] == ["turno_reservado"]
        assert body["session_id"]
        from sqlalchemy import select

        turno = await db_session.scalar(select(Turno))
        assert turno is not None and turno.cliente_id == sample_cliente.id

    async def test_sin_sesion_no_reserva(self, async_client, modelo, sample_profesional, sample_servicio):
        fake = modelo(
            _ai("", llamada("reservar_turno", profesional_id=sample_profesional.id, servicio_id=sample_servicio.id, fecha="2026-11-10", hora="10:00")),
            _ai("Para reservar tenés que iniciar sesión."),
        )
        response = await async_client.post(URL, json={"mensaje": "reservame"})
        assert response.status_code == 200
        assert response.json()["acciones"] == []
        assert "iniciar sesión" in str(fake.recibidos[1][-1].content)

    async def test_continua_la_conversacion(self, async_client, auth_headers, modelo):
        fake = modelo(_ai("¿Con quién?"), _ai("Perfecto."))
        sid = (await async_client.post(URL, json={"mensaje": "quiero un corte"}, headers=auth_headers)).json()["session_id"]
        response = await async_client.post(URL, json={"mensaje": "con Juan", "session_id": sid}, headers=auth_headers)
        assert response.json()["session_id"] == sid
        contenidos = [str(m.content) for m in fake.recibidos[1]]
        assert "quiero un corte" in contenidos and "¿Con quién?" in contenidos

    async def test_mensaje_vacio_422(self, async_client, modelo):
        modelo()
        response = await async_client.post(URL, json={"mensaje": ""})
        assert response.status_code == 422

    async def test_proveedor_caido_503(self, async_client, modelo):
        modelo(error=TimeoutError("sin respuesta"))
        response = await async_client.post(URL, json={"mensaje": "hola"})
        assert response.status_code == 503
        assert "Reservar turno" in response.json()["detail"]

    async def test_sin_key_503(self, async_client, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "CHAT_PROVIDER", "groq")
        monkeypatch.setattr(settings, "GROQ_API_KEY", "")
        response = await async_client.post(URL, json={"mensaje": "hola"})
        assert response.status_code == 503

    async def test_limite_por_minuto(self, async_client, modelo):
        modelo(*[_ai("ok") for _ in range(25)])
        codigos = [(await async_client.post(URL, json={"mensaje": f"m{i}"})).status_code for i in range(21)]
        assert codigos[:20] == [200] * 20
        assert codigos[20] == 429
