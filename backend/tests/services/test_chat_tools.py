"""CU-05/06: herramientas del chatbot contra la DB de tests."""

import json
from datetime import UTC, date, datetime

import pytest

from app.core import timeutils
from app.models.turno import Turno, TurnoEstado
from app.services.chat_tools import (
    ACCION_CANCELACION,
    ACCION_RESERVA,
    SIN_SESION,
    crear_herramientas,
    fecha_texto,
)

# 15:00 UTC = 12:00 en Buenos Aires del lunes 09/11/2026
AHORA = datetime(2026, 11, 9, 15, 0, tzinfo=UTC)
MANANA = date(2026, 11, 10)


@pytest.fixture(autouse=True)
def reloj(monkeypatch):
    monkeypatch.setattr(timeutils, "_utcnow", lambda: AHORA)


def _herramientas(db_session, cliente_id, acciones=None):
    acciones = [] if acciones is None else acciones
    return {t.name: t for t in crear_herramientas(db_session, cliente_id, acciones)}, acciones


class TestBuscarProfesionales:
    async def test_por_nombre(self, db_session, sample_profesional, sample_servicio):
        tools, _ = _herramientas(db_session, None)
        datos = json.loads(await tools["buscar_profesionales"].ainvoke({"nombre": "Juan"}))
        assert datos[0]["id"] == sample_profesional.id
        assert datos[0]["servicios"][0] == {"id": sample_servicio.id, "nombre": "Corte", "duracion_min": 30, "precio_pesos": 5000.0}

    async def test_inexistente_ofrece_los_activos(self, db_session, sample_profesional, sample_servicio):
        tools, _ = _herramientas(db_session, None)
        texto = await tools["buscar_profesionales"].ainvoke({"nombre": "Pedro"})
        assert "No hay ningún profesional llamado «Pedro»" in texto
        assert "Juan Perez" in texto


class TestConsultarDisponibilidad:
    async def test_horarios_libres(self, db_session, sample_profesional, sample_servicio, make_turno, sample_cliente):
        await make_turno(sample_cliente, sample_profesional, sample_servicio, inicio=datetime(2026, 11, 10, 10, 0, tzinfo=UTC))
        tools, _ = _herramientas(db_session, None)
        datos = json.loads(
            await tools["consultar_disponibilidad"].ainvoke(
                {"profesional_id": sample_profesional.id, "servicio_id": sample_servicio.id, "desde": MANANA.isoformat()}
            )
        )
        assert datos[MANANA.isoformat()]["dia"] == "martes 10 de noviembre"
        horas = datos[MANANA.isoformat()]["horas"]
        assert horas[0] == "09:00"
        assert "10:00" not in horas
        assert "10:30" in horas

    async def test_servicio_ajeno(self, db_session, sample_profesional):
        tools, _ = _herramientas(db_session, None)
        texto = await tools["consultar_disponibilidad"].ainvoke(
            {"profesional_id": sample_profesional.id, "servicio_id": 9999, "desde": MANANA.isoformat()}
        )
        assert texto.startswith("Error:")

    async def test_fecha_invalida(self, db_session, sample_profesional, sample_servicio):
        tools, _ = _herramientas(db_session, None)
        texto = await tools["consultar_disponibilidad"].ainvoke(
            {"profesional_id": sample_profesional.id, "servicio_id": sample_servicio.id, "desde": "mañana"}
        )
        assert texto.startswith("Error:")


class TestReservar:
    async def test_usa_el_cliente_de_la_sesion(self, db_session, sample_profesional, sample_servicio, sample_cliente):
        tools, acciones = _herramientas(db_session, sample_cliente.id)
        datos = json.loads(
            await tools["reservar_turno"].ainvoke(
                {"profesional_id": sample_profesional.id, "servicio_id": sample_servicio.id, "fecha": MANANA.isoformat(), "hora": "11:00"}
            )
        )
        turno = await db_session.get(Turno, datos["turno_id"])
        assert turno is not None and turno.cliente_id == sample_cliente.id
        assert datos["hora_inicio"] == "11:00" and datos["estado"] == "CONFIRMADO"
        assert datos["dia"] == "martes 10 de noviembre"
        assert acciones == [ACCION_RESERVA]

    async def test_sin_sesion(self, db_session, sample_profesional, sample_servicio):
        tools, acciones = _herramientas(db_session, None)
        texto = await tools["reservar_turno"].ainvoke(
            {"profesional_id": sample_profesional.id, "servicio_id": sample_servicio.id, "fecha": MANANA.isoformat(), "hora": "11:00"}
        )
        assert texto == SIN_SESION
        assert acciones == []

    async def test_horario_ocupado(self, db_session, sample_profesional, sample_servicio, sample_cliente, make_turno):
        await make_turno(sample_cliente, sample_profesional, sample_servicio, inicio=datetime(2026, 11, 10, 11, 0, tzinfo=UTC))
        tools, acciones = _herramientas(db_session, sample_cliente.id)
        texto = await tools["reservar_turno"].ainvoke(
            {"profesional_id": sample_profesional.id, "servicio_id": sample_servicio.id, "fecha": MANANA.isoformat(), "hora": "11:00"}
        )
        assert texto.startswith("Error:") and "disponible" in texto
        assert acciones == []


class TestMisTurnosYCancelar:
    async def test_mis_turnos(self, db_session, sample_profesional, sample_servicio, sample_cliente, make_turno):
        turno = await make_turno(sample_cliente, sample_profesional, sample_servicio, inicio=datetime(2026, 11, 11, 10, 0, tzinfo=UTC))
        tools, _ = _herramientas(db_session, sample_cliente.id)
        datos = json.loads(await tools["mis_turnos"].ainvoke({}))
        assert [d["turno_id"] for d in datos] == [turno.id]

    async def test_cancelar_con_antelacion(self, db_session, sample_profesional, sample_servicio, sample_cliente, make_turno):
        turno = await make_turno(sample_cliente, sample_profesional, sample_servicio, inicio=datetime(2026, 11, 11, 10, 0, tzinfo=UTC))
        tools, acciones = _herramientas(db_session, sample_cliente.id)
        datos = json.loads(await tools["cancelar_turno"].ainvoke({"turno_id": turno.id, "motivo": "Viaje"}))
        assert datos["estado"] == TurnoEstado.CANCELADO_CLIENTE.value
        assert acciones == [ACCION_CANCELACION]

    async def test_cancelar_sin_motivo(self, db_session, sample_profesional, sample_servicio, sample_cliente, make_turno):
        turno = await make_turno(sample_cliente, sample_profesional, sample_servicio, inicio=datetime(2026, 11, 11, 10, 0, tzinfo=UTC))
        tools, _ = _herramientas(db_session, sample_cliente.id)
        datos = json.loads(await tools["cancelar_turno"].ainvoke({"turno_id": turno.id}))
        assert datos["estado"] == TurnoEstado.CANCELADO_CLIENTE.value
        cancelado = await db_session.get(Turno, turno.id)
        assert cancelado is not None and cancelado.motivo_cancelacion == "Cancelado desde el chat"


class TestFechaTexto:
    def test_mismo_anio(self):
        assert fecha_texto(date(2026, 11, 7), anio_actual=2026) == "sábado 7 de noviembre"

    def test_otro_anio(self):
        assert fecha_texto(date(2027, 1, 5), anio_actual=2026) == "martes 5 de enero de 2027"

    async def test_cancelar_sobre_la_hora(self, db_session, sample_profesional, sample_servicio, sample_cliente, make_turno):
        # empieza 13:00 local, falta 1 h
        turno = await make_turno(sample_cliente, sample_profesional, sample_servicio, inicio=datetime(2026, 11, 9, 13, 0, tzinfo=UTC))
        tools, acciones = _herramientas(db_session, sample_cliente.id)
        texto = await tools["cancelar_turno"].ainvoke({"turno_id": turno.id, "motivo": "x"})
        assert texto.startswith("Error:") and "2 horas" in texto
        assert acciones == []

    async def test_cancelar_turno_ajeno(self, db_session, sample_profesional, sample_servicio, sample_cliente, make_turno):
        turno = await make_turno(sample_cliente, sample_profesional, sample_servicio, inicio=datetime(2026, 11, 11, 10, 0, tzinfo=UTC))
        tools, _ = _herramientas(db_session, sample_cliente.id + 999)
        texto = await tools["cancelar_turno"].ainvoke({"turno_id": turno.id, "motivo": "x"})
        assert texto.startswith("Error:")


class TestCalendarioTexto:
    def test_lista_proximos_dias(self) -> None:
        from datetime import datetime

        from app.services.chat_tools import calendario_texto

        texto = calendario_texto(datetime(2026, 11, 7, 10, 0), dias=5)
        assert texto.splitlines() == [
            "- hoy: 2026-11-07",
            "- mañana: 2026-11-08",
            "- lunes: 2026-11-09",
            "- martes: 2026-11-10",
            "- miércoles: 2026-11-11",
        ]
