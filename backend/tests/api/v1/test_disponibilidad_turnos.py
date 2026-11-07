"""CU-02: la grilla y las excepciones no pueden dejar turnos activos fuera de horario."""

from datetime import UTC, date, datetime, time, timedelta

import pytest

from app.core import timeutils
from app.models.turno import TurnoEstado
from app.services.disponibilidad_service import _turnos_fuera_de_horario

GRILLA = "/api/v1/profesionales/me/disponibilidad"
EXCEPCIONES = "/api/v1/profesionales/me/excepciones"
DIAS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]

# 15:00 UTC = 12:00 en Buenos Aires del lunes 09/11/2026
AHORA = datetime(2026, 11, 9, 15, 0, tzinfo=UTC)
LUNES_PROXIMO = date(2026, 11, 16)
SABADO = date(2026, 11, 14)


@pytest.fixture(autouse=True)
def reloj(monkeypatch):
    monkeypatch.setattr(timeutils, "_utcnow", lambda: AHORA)


def _grilla(**horarios: tuple[str, str] | None) -> list[dict]:
    """Grilla de 09:00 a 18:00 todos los días, salvo los indicados (None = no atiende)."""
    filas = []
    for dia in DIAS:
        horario = horarios.get(dia.lower(), ("09:00", "18:00"))
        if horario is not None:
            filas.append({"dia_semana": dia, "hora_inicio": horario[0], "hora_fin": horario[1]})
    return filas


@pytest.fixture
def turno_en(make_turno, sample_cliente, sample_profesional, sample_servicio):
    async def crear(fecha: date, hora: time, estado: TurnoEstado = TurnoEstado.CONFIRMADO):
        inicio = datetime.combine(fecha, hora, tzinfo=UTC)
        return await make_turno(sample_cliente, sample_profesional, sample_servicio, inicio=inicio, estado=estado)

    return crear


class TestHelper:
    class _T:
        def __init__(self, inicio: datetime, minutos: int = 30):
            self.fecha_inicio = inicio
            self.fecha_fin = inicio + timedelta(minutes=minutos)

    def _afuera(self, inicio: datetime, horario):
        return _turnos_fuera_de_horario([self._T(inicio)], lambda _f: horario)

    def test_dentro(self):
        assert self._afuera(datetime(2026, 11, 16, 10, 0), (time(9), time(18))) == []

    def test_empieza_antes(self):
        assert len(self._afuera(datetime(2026, 11, 16, 8, 45), (time(9), time(18)))) == 1

    def test_termina_despues(self):
        assert len(self._afuera(datetime(2026, 11, 16, 17, 45), (time(9), time(18)))) == 1

    def test_dia_sin_atencion(self):
        assert len(self._afuera(datetime(2026, 11, 16, 10, 0), None)) == 1


class TestGrilla:
    async def test_acortar_sin_turnos_afectados(self, async_client, proveedor_headers, turno_en):
        await turno_en(LUNES_PROXIMO, time(10, 0))
        response = await async_client.put(GRILLA, json=_grilla(lunes=("09:00", "13:00")), headers=proveedor_headers)
        assert response.status_code == 200, response.text

    async def test_acortar_con_turno_afectado(self, async_client, proveedor_headers, turno_en):
        await turno_en(LUNES_PROXIMO, time(15, 0))
        response = await async_client.put(GRILLA, json=_grilla(lunes=("09:00", "13:00")), headers=proveedor_headers)
        assert response.status_code == 409
        assert "1 turno" in response.json()["detail"]
        assert "16/11 15:00" in response.json()["detail"]

        grilla = (await async_client.get(GRILLA, headers=proveedor_headers)).json()["grilla"]
        lunes = next(d for d in grilla if d["dia_semana"] == "LUNES")
        assert lunes["hora_fin"].startswith("18:00")

    async def test_dejar_de_atender_un_dia(self, async_client, proveedor_headers, turno_en):
        await turno_en(SABADO, time(10, 0), TurnoEstado.PENDIENTE)
        response = await async_client.put(GRILLA, json=_grilla(sabado=None), headers=proveedor_headers)
        assert response.status_code == 409

    async def test_cancelados_y_pasados_no_bloquean(self, async_client, proveedor_headers, turno_en):
        await turno_en(SABADO, time(10, 0), TurnoEstado.CANCELADO_CLIENTE)
        await turno_en(date(2026, 11, 7), time(10, 0))  # sábado anterior, ya pasó
        response = await async_client.put(GRILLA, json=_grilla(sabado=None), headers=proveedor_headers)
        assert response.status_code == 200, response.text

    async def test_excepcion_existente_manda(self, async_client, proveedor_headers, turno_en):
        await turno_en(SABADO, time(10, 0))
        alta = await async_client.post(
            EXCEPCIONES,
            json={"fecha": SABADO.isoformat(), "tipo": "HORARIO_ESPECIAL", "hora_inicio": "09:00", "hora_fin": "12:00"},
            headers=proveedor_headers,
        )
        assert alta.status_code == 201, alta.text
        response = await async_client.put(GRILLA, json=_grilla(sabado=None), headers=proveedor_headers)
        assert response.status_code == 200, response.text


class TestExcepciones:
    async def test_cerrar_dia_con_turnos(self, async_client, proveedor_headers, turno_en):
        await turno_en(LUNES_PROXIMO, time(10, 0))
        response = await async_client.post(
            EXCEPCIONES, json={"fecha": LUNES_PROXIMO.isoformat(), "tipo": "CERRADO"}, headers=proveedor_headers
        )
        assert response.status_code == 409
        listado = await async_client.get(EXCEPCIONES, headers=proveedor_headers)
        assert listado.json() == []

    async def test_horario_especial_compatible(self, async_client, proveedor_headers, turno_en):
        await turno_en(LUNES_PROXIMO, time(10, 0))
        response = await async_client.post(
            EXCEPCIONES,
            json={
                "fecha": LUNES_PROXIMO.isoformat(),
                "tipo": "HORARIO_ESPECIAL",
                "hora_inicio": "09:00",
                "hora_fin": "12:00",
            },
            headers=proveedor_headers,
        )
        assert response.status_code == 201, response.text

    async def test_horario_especial_incompatible(self, async_client, proveedor_headers, turno_en):
        await turno_en(LUNES_PROXIMO, time(15, 0))
        response = await async_client.post(
            EXCEPCIONES,
            json={
                "fecha": LUNES_PROXIMO.isoformat(),
                "tipo": "HORARIO_ESPECIAL",
                "hora_inicio": "09:00",
                "hora_fin": "12:00",
            },
            headers=proveedor_headers,
        )
        assert response.status_code == 409

    async def test_otro_dia_no_bloquea(self, async_client, proveedor_headers, turno_en):
        await turno_en(LUNES_PROXIMO, time(10, 0))
        response = await async_client.post(
            EXCEPCIONES, json={"fecha": SABADO.isoformat(), "tipo": "CERRADO"}, headers=proveedor_headers
        )
        assert response.status_code == 201, response.text
