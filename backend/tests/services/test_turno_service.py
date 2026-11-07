"""Unit tests for TurnoService - CU-03 Turnos y Reservas (real DB)."""

from datetime import UTC, datetime, time, timedelta

import pytest

from app.core.timeutils import ahora_negocio
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.profesional import Servicio
from app.models.turno import TurnoEstado
from app.schemas.turno import ChatbotReservarRequest
from app.services.turno_service import TurnoService
from tests.conftest import proximo_dia_habil


def _dt(dias: int, hora: int, minuto: int = 0) -> datetime:
    return datetime.combine(proximo_dia_habil(dias), time(hora, minuto), tzinfo=UTC)


class TestConstantes:
    def test_cancelacion_cliente_horas_antes(self):
        assert TurnoService.CANCELACION_CLIENTE_HORAS_ANTES == 2

    def test_estados_finales_sin_transiciones(self):
        for estado in (
            TurnoEstado.FINALIZADO,
            TurnoEstado.CANCELADO_CLIENTE,
            TurnoEstado.CANCELADO_PROFESIONAL,
            TurnoEstado.NO_ASISTIO,
        ):
            assert TurnoService.TRANSICIONES_VALIDAS[estado] == []

    def test_matriz_cubre_todos_los_estados(self):
        assert set(TurnoService.TRANSICIONES_VALIDAS) == set(TurnoEstado)


class TestConsultarDisponibilidad:
    async def test_devuelve_slots_del_profesional(self, db_session, sample_profesional, sample_servicio):
        dia = proximo_dia_habil(2)
        result = await TurnoService(db_session).consultar_disponibilidad(
            profesional_id=sample_profesional.id, servicio_id=sample_servicio.id, desde=dia, hasta=dia
        )
        assert len(result.profesionales) == 1
        slots = result.profesionales[0].slots_por_fecha[dia.isoformat()]
        # 09:00-18:00 en slots de 30 min
        assert len(slots) == 18
        assert slots[0].hora_inicio == time(9, 0)

    async def test_sin_filtros_incluye_todos_los_activos(self, db_session, make_profesional):
        await make_profesional(nombre="Ana")
        await make_profesional(nombre="Beto")
        await make_profesional(nombre="Inactivo", activo=False)
        dia = proximo_dia_habil(2)
        result = await TurnoService(db_session).consultar_disponibilidad(
            profesional_id=None, servicio_id=None, desde=dia, hasta=dia
        )
        nombres = {p.profesional_nombre.split()[0] for p in result.profesionales}
        assert nombres == {"Ana", "Beto"}

    async def test_servicio_de_otro_profesional_lo_excluye(
        self, db_session, make_profesional, sample_servicio
    ):
        otro = await make_profesional(nombre="Otro")
        dia = proximo_dia_habil(2)
        result = await TurnoService(db_session).consultar_disponibilidad(
            profesional_id=otro.id, servicio_id=sample_servicio.id, desde=dia, hasta=dia
        )
        assert result.profesionales == []

    async def test_turno_ocupa_slot(self, db_session, sample_turno, sample_profesional):
        dia = sample_turno.fecha_inicio.date()
        result = await TurnoService(db_session).consultar_disponibilidad(
            profesional_id=sample_profesional.id, servicio_id=None, desde=dia, hasta=dia
        )
        slots = result.profesionales[0].slots_por_fecha[dia.isoformat()]
        slot_10 = next(s for s in slots if s.hora_inicio == time(10, 0))
        assert slot_10.disponible is False


class TestCrearReservaManual:
    async def test_exitosa_queda_confirmada(self, db_session, sample_cliente, sample_profesional, sample_servicio):
        result = await TurnoService(db_session).crear_reserva_manual(
            cliente_id=sample_cliente.id,
            profesional_id=sample_profesional.id,
            servicio_id=sample_servicio.id,
            fecha=proximo_dia_habil(1),
            hora_inicio=time(9, 0),
        )
        assert result.estado == TurnoEstado.CONFIRMADO
        assert result.cliente_id == sample_cliente.id
        assert result.fecha_fin - result.fecha_inicio == timedelta(minutes=30)
        assert result.confirmado_en is not None

    async def test_slot_ocupado_conflict(self, db_session, sample_cliente, sample_profesional, sample_servicio):
        service = TurnoService(db_session)
        kwargs = dict(
            cliente_id=sample_cliente.id,
            profesional_id=sample_profesional.id,
            servicio_id=sample_servicio.id,
            fecha=proximo_dia_habil(1),
            hora_inicio=time(9, 0),
        )
        await service.crear_reserva_manual(**kwargs)
        with pytest.raises(ConflictException):
            await service.crear_reserva_manual(**kwargs)

    async def test_solapamiento_parcial_conflict(
        self, db_session, sample_cliente, sample_profesional, sample_servicio
    ):
        largo = Servicio(profesional_id=sample_profesional.id, nombre="Color", duracion_min=60, precio=100)
        db_session.add(largo)
        await db_session.commit()
        service = TurnoService(db_session)
        await service.crear_reserva_manual(
            cliente_id=sample_cliente.id,
            profesional_id=sample_profesional.id,
            servicio_id=largo.id,
            fecha=proximo_dia_habil(1),
            hora_inicio=time(9, 0),
        )
        with pytest.raises(ConflictException):
            await service.crear_reserva_manual(
                cliente_id=sample_cliente.id,
                profesional_id=sample_profesional.id,
                servicio_id=sample_servicio.id,
                fecha=proximo_dia_habil(1),
                hora_inicio=time(9, 30),
            )

    async def test_en_el_pasado_rechazada(self, db_session, sample_cliente, sample_profesional, sample_servicio):
        with pytest.raises(ValidationException):
            await TurnoService(db_session).crear_reserva_manual(
                cliente_id=sample_cliente.id,
                profesional_id=sample_profesional.id,
                servicio_id=sample_servicio.id,
                fecha=proximo_dia_habil(-1),
                hora_inicio=time(9, 0),
            )

    async def test_servicio_de_otro_profesional(self, db_session, sample_cliente, make_profesional, sample_servicio):
        otro = await make_profesional(nombre="Otro")
        with pytest.raises(NotFoundException):
            await TurnoService(db_session).crear_reserva_manual(
                cliente_id=sample_cliente.id,
                profesional_id=otro.id,
                servicio_id=sample_servicio.id,
                fecha=proximo_dia_habil(1),
                hora_inicio=time(9, 0),
            )

    async def test_profesional_inactivo(self, db_session, sample_cliente, sample_profesional, sample_servicio):
        sample_profesional.activo = False
        await db_session.commit()
        with pytest.raises(NotFoundException):
            await TurnoService(db_session).crear_reserva_manual(
                cliente_id=sample_cliente.id,
                profesional_id=sample_profesional.id,
                servicio_id=sample_servicio.id,
                fecha=proximo_dia_habil(1),
                hora_inicio=time(9, 0),
            )

    async def test_cliente_inexistente(self, db_session, sample_profesional, sample_servicio):
        with pytest.raises(NotFoundException):
            await TurnoService(db_session).crear_reserva_manual(
                cliente_id=9999,
                profesional_id=sample_profesional.id,
                servicio_id=sample_servicio.id,
                fecha=proximo_dia_habil(1),
                hora_inicio=time(9, 0),
            )


class TestCancelarTurnoCliente:
    async def test_futuro_se_cancela(self, db_session, sample_turno, sample_cliente):
        result = await TurnoService(db_session).cancelar_turno_cliente(
            turno_id=sample_turno.id, cliente_id=sample_cliente.id, motivo="No puedo ir"
        )
        assert result.estado == TurnoEstado.CANCELADO_CLIENTE
        assert result.cancelado_por == "cliente"
        assert result.motivo_cancelacion == "No puedo ir"

    async def test_con_menos_de_2h_rechazado(
        self, db_session, make_turno, sample_cliente, sample_profesional, sample_servicio
    ):
        turno = await make_turno(
            sample_cliente, sample_profesional, sample_servicio, inicio=ahora_negocio() + timedelta(hours=1)
        )
        with pytest.raises(ValidationException):
            await TurnoService(db_session).cancelar_turno_cliente(
                turno_id=turno.id, cliente_id=sample_cliente.id, motivo="tarde"
            )

    async def test_turno_ajeno_404(self, db_session, sample_turno):
        with pytest.raises(NotFoundException):
            await TurnoService(db_session).cancelar_turno_cliente(
                turno_id=sample_turno.id, cliente_id=sample_turno.cliente_id + 100, motivo="x"
            )

    async def test_ya_finalizado_rechazado(
        self, db_session, make_turno, sample_cliente, sample_profesional, sample_servicio
    ):
        turno = await make_turno(sample_cliente, sample_profesional, sample_servicio, estado=TurnoEstado.FINALIZADO)
        with pytest.raises(ValidationException):
            await TurnoService(db_session).cancelar_turno_cliente(
                turno_id=turno.id, cliente_id=sample_cliente.id, motivo="x"
            )


class TestCancelarTurnoProfesional:
    async def test_futuro_se_cancela(self, db_session, sample_turno, sample_profesional):
        result = await TurnoService(db_session).cancelar_turno_profesional(
            turno_id=sample_turno.id, profesional_id=sample_profesional.id, motivo="Enfermo"
        )
        assert result.estado == TurnoEstado.CANCELADO_PROFESIONAL
        assert result.cancelado_por == "profesional"

    async def test_finalizado_rechazado(
        self, db_session, make_turno, sample_cliente, sample_profesional, sample_servicio
    ):
        turno = await make_turno(sample_cliente, sample_profesional, sample_servicio, estado=TurnoEstado.FINALIZADO)
        with pytest.raises(ValidationException):
            await TurnoService(db_session).cancelar_turno_profesional(
                turno_id=turno.id, profesional_id=sample_profesional.id, motivo="x"
            )

    async def test_turno_de_otro_profesional_404(self, db_session, sample_turno, make_profesional):
        otro = await make_profesional(nombre="Otro")
        with pytest.raises(NotFoundException):
            await TurnoService(db_session).cancelar_turno_profesional(
                turno_id=sample_turno.id, profesional_id=otro.id, motivo="x"
            )


class TestCambiarEstado:
    async def test_transicion_valida(self, db_session, sample_turno, sample_profesional):
        result = await TurnoService(db_session).cambiar_estado(
            sample_turno.id, sample_profesional.id, TurnoEstado.EN_CURSO
        )
        assert result.estado == TurnoEstado.EN_CURSO

    async def test_finalizar_registra_timestamp(
        self, db_session, make_turno, sample_cliente, sample_profesional, sample_servicio
    ):
        turno = await make_turno(sample_cliente, sample_profesional, sample_servicio, estado=TurnoEstado.EN_CURSO)
        result = await TurnoService(db_session).cambiar_estado(
            turno.id, sample_profesional.id, TurnoEstado.FINALIZADO
        )
        assert result.estado == TurnoEstado.FINALIZADO
        assert result.finalizado_en is not None

    async def test_transicion_invalida(self, db_session, sample_turno, sample_profesional):
        with pytest.raises(ValidationException):
            await TurnoService(db_session).cambiar_estado(
                sample_turno.id, sample_profesional.id, TurnoEstado.FINALIZADO
            )


class TestReasignarTurno:
    async def test_a_slot_libre(self, db_session, sample_turno, sample_profesional):
        nueva = proximo_dia_habil(4)
        result = await TurnoService(db_session).reasignar_turno(
            turno_id=sample_turno.id,
            profesional_id=sample_profesional.id,
            nueva_fecha=nueva,
            nueva_hora_inicio=time(15, 0),
            motivo="Cambio de agenda",
        )
        assert result.fecha_inicio.replace(tzinfo=UTC) == _dt(4, 15)
        assert result.fecha_fin - result.fecha_inicio == timedelta(minutes=30)

    async def test_corrimiento_solapado_con_si_mismo_permitido(
        self, db_session, make_turno, sample_cliente, sample_profesional, servicio_largo
    ):
        # 60 min: 10:00-11:00 -> 10:30-11:30 solo se solapa con el propio turno
        turno = await make_turno(sample_cliente, sample_profesional, servicio_largo)
        result = await TurnoService(db_session).reasignar_turno(
            turno_id=turno.id,
            profesional_id=sample_profesional.id,
            nueva_fecha=turno.fecha_inicio.date(),
            nueva_hora_inicio=time(10, 30),
            motivo="Corrimiento",
        )
        assert result.fecha_inicio.replace(tzinfo=UTC).time() == time(10, 30)
        assert result.fecha_fin.replace(tzinfo=UTC).time() == time(11, 30)

    async def test_inicio_desalineado_422(self, db_session, sample_turno, sample_profesional):
        with pytest.raises(ValidationException):
            await TurnoService(db_session).reasignar_turno(
                turno_id=sample_turno.id,
                profesional_id=sample_profesional.id,
                nueva_fecha=sample_turno.fecha_inicio.date(),
                nueva_hora_inicio=time(10, 15),
                motivo="x",
            )

    async def test_a_slot_ocupado_conflict(
        self, db_session, make_turno, sample_turno, sample_cliente, sample_profesional, sample_servicio
    ):
        await make_turno(sample_cliente, sample_profesional, sample_servicio, inicio=_dt(4, 15))
        with pytest.raises(ConflictException):
            await TurnoService(db_session).reasignar_turno(
                turno_id=sample_turno.id,
                profesional_id=sample_profesional.id,
                nueva_fecha=proximo_dia_habil(4),
                nueva_hora_inicio=time(15, 0),
                motivo="x",
            )

    async def test_finalizado_no_se_reasigna(
        self, db_session, make_turno, sample_cliente, sample_profesional, sample_servicio
    ):
        turno = await make_turno(sample_cliente, sample_profesional, sample_servicio, estado=TurnoEstado.FINALIZADO)
        with pytest.raises(ValidationException):
            await TurnoService(db_session).reasignar_turno(
                turno_id=turno.id,
                profesional_id=sample_profesional.id,
                nueva_fecha=proximo_dia_habil(4),
                nueva_hora_inicio=time(15, 0),
                motivo="x",
            )


class TestNotasProfesional:
    async def test_agregar_notas(self, db_session, sample_turno, sample_profesional):
        result = await TurnoService(db_session).agregar_notas_profesional(
            sample_turno.id, sample_profesional.id, "Prefiere corte seco"
        )
        assert result.notas_profesional == "Prefiere corte seco"


class TestCrearTurnoDesdeChatbot:
    async def test_exitoso(self, db_session, sample_cliente, sample_profesional, sample_servicio):
        result = await TurnoService(db_session).crear_turno_desde_chatbot(
            ChatbotReservarRequest(
                cliente_id=sample_cliente.id,
                profesional_id=sample_profesional.id,
                servicio_id=sample_servicio.id,
                fecha=proximo_dia_habil(1),
                hora_inicio=time(11, 0),
            )
        )
        assert result.turno_id > 0
        assert result.estado == TurnoEstado.CONFIRMADO
        assert result.servicio_nombre == "Corte"
        assert result.profesional_nombre == "Juan Perez"
        assert result.hora_fin.replace(tzinfo=None) == time(11, 30)

    async def test_slot_ocupado(self, db_session, sample_turno, sample_cliente, sample_profesional, sample_servicio):
        with pytest.raises(ConflictException):
            await TurnoService(db_session).crear_turno_desde_chatbot(
                ChatbotReservarRequest(
                    cliente_id=sample_cliente.id,
                    profesional_id=sample_profesional.id,
                    servicio_id=sample_servicio.id,
                    fecha=sample_turno.fecha_inicio.date(),
                    hora_inicio=time(10, 0),
                )
            )


class TestHoraNegocio:
    """Las reglas que dependen de "ahora" usan la hora local del negocio (UTC-3)."""

    @pytest.fixture
    def reloj(self, monkeypatch):
        from app.core import timeutils

        def _set(utc: datetime) -> None:
            monkeypatch.setattr(timeutils, "_utcnow", lambda: utc)

        return _set

    async def test_cancelacion_con_hora_local(
        self, db_session, reloj, make_turno, sample_cliente, sample_profesional, sample_servicio
    ):
        # 23:00 UTC = 20:00 en Buenos Aires; el turno es a las 23:00 locales -> faltan 3 h
        reloj(datetime(2026, 11, 2, 23, 0, tzinfo=UTC))
        turno = await make_turno(
            sample_cliente, sample_profesional, sample_servicio, inicio=datetime(2026, 11, 2, 23, 0, tzinfo=UTC)
        )
        result = await TurnoService(db_session).cancelar_turno_cliente(
            turno_id=turno.id, cliente_id=sample_cliente.id, motivo="x"
        )
        assert result.estado == TurnoEstado.CANCELADO_CLIENTE

    async def test_reserva_no_se_considera_pasada_por_utc(
        self, db_session, reloj, sample_cliente, sample_profesional, sample_servicio
    ):
        # 13:00 UTC = 10:00 locales: reservar a las 11:00 de hoy es válido
        reloj(datetime(2026, 11, 2, 13, 0, tzinfo=UTC))
        result = await TurnoService(db_session).crear_reserva_manual(
            cliente_id=sample_cliente.id,
            profesional_id=sample_profesional.id,
            servicio_id=sample_servicio.id,
            fecha=datetime(2026, 11, 2).date(),
            hora_inicio=time(11, 0),
        )
        assert result.estado == TurnoEstado.CONFIRMADO


class TestSlotsConDuracionDelServicio:
    async def _slots(self, db_session, profesional, servicio, dia):
        result = await TurnoService(db_session).consultar_disponibilidad(
            profesional_id=profesional.id, servicio_id=servicio.id, desde=dia, hasta=dia
        )
        return {s.hora_inicio: s for s in result.profesionales[0].slots_por_fecha[dia.isoformat()]}

    async def test_servicio_largo_antes_de_turno_ocupado(
        self, db_session, sample_turno, sample_profesional, servicio_largo
    ):
        # sample_turno ocupa 10:00-10:30
        slots = await self._slots(db_session, sample_profesional, servicio_largo, sample_turno.fecha_inicio.date())
        assert slots[time(9, 0)].disponible is True
        assert slots[time(9, 30)].disponible is False
        assert slots[time(9, 0)].hora_fin == time(10, 0)

    async def test_servicio_largo_al_cierre(self, db_session, sample_profesional, servicio_largo):
        slots = await self._slots(db_session, sample_profesional, servicio_largo, proximo_dia_habil(2))
        # cierra 18:00: el último inicio posible para 60 min es 17:00
        assert time(17, 0) in slots
        assert time(17, 30) not in slots

    async def test_sin_servicio_usa_duracion_de_slot(self, db_session, sample_profesional):
        dia = proximo_dia_habil(2)
        result = await TurnoService(db_session).consultar_disponibilidad(
            profesional_id=sample_profesional.id, servicio_id=None, desde=dia, hasta=dia
        )
        slots = result.profesionales[0].slots_por_fecha[dia.isoformat()]
        assert slots[-1].hora_inicio == time(17, 30)

    async def test_slots_de_hoy_que_ya_pasaron(
        self, db_session, monkeypatch, sample_profesional, sample_servicio
    ):
        from app.core import timeutils

        # 15:00 UTC = 12:00 en Buenos Aires
        monkeypatch.setattr(timeutils, "_utcnow", lambda: datetime(2026, 11, 2, 15, 0, tzinfo=UTC))
        hoy = datetime(2026, 11, 2).date()
        slots = await self._slots(db_session, sample_profesional, sample_servicio, hoy)
        assert slots[time(11, 30)].disponible is False
        assert slots[time(12, 0)].disponible is False  # empieza justo ahora
        assert slots[time(12, 30)].disponible is True


class TestReservaDentroDelHorario:
    async def _reservar(self, db_session, cliente, profesional, servicio, hora, dias=2):
        return await TurnoService(db_session).crear_reserva_manual(
            cliente_id=cliente.id,
            profesional_id=profesional.id,
            servicio_id=servicio.id,
            fecha=proximo_dia_habil(dias),
            hora_inicio=hora,
        )

    async def test_dentro_del_horario(self, db_session, sample_cliente, sample_profesional, sample_servicio):
        result = await self._reservar(db_session, sample_cliente, sample_profesional, sample_servicio, time(10, 0))
        assert result.fecha_fin.time() == time(10, 30)

    async def test_fuera_del_horario(self, db_session, sample_cliente, sample_profesional, sample_servicio):
        with pytest.raises(ValidationException):
            await self._reservar(db_session, sample_cliente, sample_profesional, sample_servicio, time(7, 0))

    async def test_servicio_no_entra_antes_del_cierre(
        self, db_session, sample_cliente, sample_profesional, servicio_largo
    ):
        with pytest.raises(ValidationException):
            await self._reservar(db_session, sample_cliente, sample_profesional, servicio_largo, time(17, 30))

    async def test_inicio_desalineado(self, db_session, sample_cliente, sample_profesional, sample_servicio):
        with pytest.raises(ValidationException):
            await self._reservar(db_session, sample_cliente, sample_profesional, sample_servicio, time(9, 10))

    async def test_dia_sin_grilla(self, db_session, sample_cliente, sample_profesional, sample_servicio):
        from sqlalchemy import delete

        from app.models.profesional import DiaSemana, Disponibilidad

        dia = proximo_dia_habil(2)
        await db_session.execute(
            delete(Disponibilidad).where(
                Disponibilidad.profesional_id == sample_profesional.id,
                Disponibilidad.dia_semana == list(DiaSemana)[dia.weekday()],
            )
        )
        await db_session.commit()
        with pytest.raises(ValidationException):
            await self._reservar(db_session, sample_cliente, sample_profesional, sample_servicio, time(10, 0))

    async def test_dia_cerrado_por_excepcion(self, db_session, sample_cliente, sample_profesional, sample_servicio):
        from app.models.profesional import ExcepcionDisponibilidad, TipoExcepcion

        db_session.add(
            ExcepcionDisponibilidad(
                profesional_id=sample_profesional.id, fecha=proximo_dia_habil(2), tipo=TipoExcepcion.CERRADO
            )
        )
        await db_session.commit()
        with pytest.raises(ValidationException):
            await self._reservar(db_session, sample_cliente, sample_profesional, sample_servicio, time(10, 0))

    async def test_horario_especial(self, db_session, sample_cliente, sample_profesional, sample_servicio):
        from app.models.profesional import ExcepcionDisponibilidad, TipoExcepcion

        db_session.add(
            ExcepcionDisponibilidad(
                profesional_id=sample_profesional.id,
                fecha=proximo_dia_habil(2),
                tipo=TipoExcepcion.HORARIO_ESPECIAL,
                hora_inicio=time(10, 0),
                hora_fin=time(14, 0),
            )
        )
        await db_session.commit()
        with pytest.raises(ValidationException):
            await self._reservar(db_session, sample_cliente, sample_profesional, sample_servicio, time(15, 0))
        ok = await self._reservar(db_session, sample_cliente, sample_profesional, sample_servicio, time(13, 30))
        assert ok.estado == TurnoEstado.CONFIRMADO


class TestMarcarAusencia:
    async def test_despues_de_la_hora(
        self, db_session, monkeypatch, make_turno, sample_cliente, sample_profesional, sample_servicio
    ):
        from app.core import timeutils

        # 13:20 UTC = 10:20 locales; el turno empezaba a las 10:00
        monkeypatch.setattr(timeutils, "_utcnow", lambda: datetime(2026, 11, 2, 13, 20, tzinfo=UTC))
        turno = await make_turno(
            sample_cliente, sample_profesional, sample_servicio, inicio=datetime(2026, 11, 2, 10, 0, tzinfo=UTC)
        )
        result = await TurnoService(db_session).cambiar_estado(turno.id, sample_profesional.id, TurnoEstado.NO_ASISTIO)
        assert result.estado == TurnoEstado.NO_ASISTIO

    async def test_antes_de_la_hora(
        self, db_session, monkeypatch, make_turno, sample_cliente, sample_profesional, sample_servicio
    ):
        from app.core import timeutils

        # 12:00 UTC = 09:00 locales
        monkeypatch.setattr(timeutils, "_utcnow", lambda: datetime(2026, 11, 2, 12, 0, tzinfo=UTC))
        turno = await make_turno(
            sample_cliente, sample_profesional, sample_servicio, inicio=datetime(2026, 11, 2, 10, 0, tzinfo=UTC)
        )
        with pytest.raises(ValidationException):
            await TurnoService(db_session).cambiar_estado(turno.id, sample_profesional.id, TurnoEstado.NO_ASISTIO)
        await db_session.refresh(turno)
        assert turno.estado == TurnoEstado.CONFIRMADO


class TestReasignacionCU08:
    """CU-08: la reasignación se valida contra los slots y queda auditada."""

    async def _reasignar(self, db_session, turno, profesional, dias, hora, motivo="Enfermedad"):
        return await TurnoService(db_session).reasignar_turno(
            turno_id=turno.id,
            profesional_id=profesional.id,
            nueva_fecha=proximo_dia_habil(dias),
            nueva_hora_inicio=hora,
            motivo=motivo,
        )

    async def test_slot_libre_libera_el_anterior_y_audita(
        self, db_session, sample_turno, sample_profesional, sample_servicio
    ):
        anterior = sample_turno.fecha_inicio.replace(tzinfo=UTC)
        result = await self._reasignar(db_session, sample_turno, sample_profesional, 4, time(15, 0))

        assert result.fecha_inicio.replace(tzinfo=UTC) == _dt(4, 15)
        assert result.reasignado_desde is not None
        assert result.reasignado_desde.replace(tzinfo=UTC) == anterior
        assert result.motivo_reasignacion == "Enfermedad"
        assert result.reasignado_en is not None

        dia = anterior.date()
        disp = await TurnoService(db_session).consultar_disponibilidad(
            profesional_id=sample_profesional.id, servicio_id=sample_servicio.id, desde=dia, hasta=dia
        )
        slots = {s.hora_inicio: s for s in disp.profesionales[0].slots_por_fecha[dia.isoformat()]}
        assert slots[time(10, 0)].disponible is True

    async def test_fuera_de_horario_422(self, db_session, sample_turno, sample_profesional):
        anterior = sample_turno.fecha_inicio
        with pytest.raises(ValidationException):
            await self._reasignar(db_session, sample_turno, sample_profesional, 4, time(3, 0))
        await db_session.refresh(sample_turno)
        assert sample_turno.fecha_inicio == anterior
        assert sample_turno.reasignado_en is None

    async def test_dia_cerrado_422(self, db_session, sample_turno, sample_profesional):
        from app.models.profesional import ExcepcionDisponibilidad, TipoExcepcion

        db_session.add(
            ExcepcionDisponibilidad(
                profesional_id=sample_profesional.id, fecha=proximo_dia_habil(4), tipo=TipoExcepcion.CERRADO
            )
        )
        await db_session.commit()
        with pytest.raises(ValidationException):
            await self._reasignar(db_session, sample_turno, sample_profesional, 4, time(15, 0))

    async def test_al_pasado_422(self, db_session, sample_turno, sample_profesional):
        with pytest.raises(ValidationException):
            await self._reasignar(db_session, sample_turno, sample_profesional, -1, time(15, 0))

    async def test_segunda_reasignacion_conserva_solo_la_ultima(
        self, db_session, sample_turno, sample_profesional
    ):
        await self._reasignar(db_session, sample_turno, sample_profesional, 4, time(15, 0), motivo="Primera")
        result = await self._reasignar(db_session, sample_turno, sample_profesional, 5, time(11, 0), motivo="Segunda")
        assert result.motivo_reasignacion == "Segunda"
        assert result.reasignado_desde is not None
        assert result.reasignado_desde.replace(tzinfo=UTC) == _dt(4, 15)


class TestCancelacionProfesionalCU08:
    @pytest.fixture
    def reloj(self, monkeypatch):
        from app.core import timeutils

        # 13:20 UTC = 10:20 en Buenos Aires
        monkeypatch.setattr(timeutils, "_utcnow", lambda: datetime(2026, 11, 2, 13, 20, tzinfo=UTC))

    async def test_turno_ya_empezado_422(
        self, db_session, reloj, make_turno, sample_cliente, sample_profesional, sample_servicio
    ):
        turno = await make_turno(
            sample_cliente, sample_profesional, sample_servicio, inicio=datetime(2026, 11, 2, 10, 0, tzinfo=UTC)
        )
        with pytest.raises(ValidationException):
            await TurnoService(db_session).cancelar_turno_profesional(
                turno_id=turno.id, profesional_id=sample_profesional.id, motivo="Corte de luz"
            )

    async def test_en_curso_se_cancela(
        self, db_session, reloj, make_turno, sample_cliente, sample_profesional, sample_servicio
    ):
        turno = await make_turno(
            sample_cliente,
            sample_profesional,
            sample_servicio,
            inicio=datetime(2026, 11, 2, 10, 0, tzinfo=UTC),
            estado=TurnoEstado.EN_CURSO,
        )
        result = await TurnoService(db_session).cancelar_turno_profesional(
            turno_id=turno.id, profesional_id=sample_profesional.id, motivo="Corte de luz"
        )
        assert result.estado == TurnoEstado.CANCELADO_PROFESIONAL

    async def test_futuro_se_cancela_y_libera_el_slot(
        self, db_session, reloj, make_turno, sample_cliente, sample_profesional, sample_servicio
    ):
        turno = await make_turno(
            sample_cliente, sample_profesional, sample_servicio, inicio=datetime(2026, 11, 3, 10, 0, tzinfo=UTC)
        )
        result = await TurnoService(db_session).cancelar_turno_profesional(
            turno_id=turno.id, profesional_id=sample_profesional.id, motivo="Corte de luz"
        )
        assert result.estado == TurnoEstado.CANCELADO_PROFESIONAL
        assert result.motivo_cancelacion == "Corte de luz"

        dia = datetime(2026, 11, 3).date()
        disp = await TurnoService(db_session).consultar_disponibilidad(
            profesional_id=sample_profesional.id, servicio_id=sample_servicio.id, desde=dia, hasta=dia
        )
        slots = {s.hora_inicio: s for s in disp.profesionales[0].slots_por_fecha[dia.isoformat()]}
        assert slots[time(10, 0)].disponible is True


class TestSlotsExcluyendoTurno:
    async def test_excluido_figura_disponible(self, db_session, sample_turno, sample_profesional, sample_servicio):
        dia = sample_turno.fecha_inicio.date()
        service = TurnoService(db_session)

        sin_excluir = await service.obtener_slots_profesional(sample_profesional.id, dia, dia, sample_servicio.id)
        excluyendo = await service.obtener_slots_profesional(
            sample_profesional.id, dia, dia, sample_servicio.id, excluir_turno_id=sample_turno.id
        )
        a_las_10 = time(10, 0)
        assert next(s for s in sin_excluir.slots if s.hora_inicio == a_las_10).disponible is False
        assert next(s for s in excluyendo.slots if s.hora_inicio == a_las_10).disponible is True

    async def test_servicio_ajeno_404(self, db_session, sample_profesional, make_profesional):
        otro = await make_profesional(nombre="Otro")
        ajeno = Servicio(profesional_id=otro.id, nombre="Ajeno", duracion_min=30, precio=1)
        db_session.add(ajeno)
        await db_session.commit()
        dia = proximo_dia_habil(2)
        with pytest.raises(NotFoundException):
            await TurnoService(db_session).obtener_slots_profesional(sample_profesional.id, dia, dia, ajeno.id)
