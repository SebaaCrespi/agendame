"""Datos de prueba para desarrollo (idempotente).

Uso (desde backend/):
    python scripts/seed_dev.py

Credenciales de prueba (solo desarrollo local):
    admin@agendame.com    / Admin12345   (ADMIN)
    juan@agendame.com     / Prof12345    (PROVEEDOR) - Juan Pérez, lun-sáb 09:00-18:00
    maria@agendame.com    / Prof12345    (PROVEEDOR) - María Gómez, lun-vie 10:00-19:00
    cliente@agendame.com  / Cliente12345 (CLIENTE)
    ana@agendame.com      / Cliente12345 (CLIENTE) - Ana López
    beto@agendame.com     / Cliente12345 (CLIENTE) - Beto Ruiz

También crea turnos de ejemplo para Juan en la semana actual (creado_por="seed"),
salteando los horarios que ya estén ocupados.

Además crea el perfil Cliente que falte a usuarios CLIENTE registrados antes
de que el registro lo creara automáticamente.
"""

import asyncio
import sys
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.database import async_session_maker, init_db  # noqa: E402
from app.core.timeutils import ahora_negocio  # noqa: E402
from app.models.cliente import Cliente  # noqa: E402
from app.models.profesional import DiaSemana, Disponibilidad, Profesional, Servicio  # noqa: E402
from app.models.turno import Turno, TurnoEstado  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.repositories.user_repo import UserRepo  # noqa: E402

LUN_SAB = [d for d in DiaSemana if d != DiaSemana.DOMINGO]
LUN_VIE = LUN_SAB[:5]

PROFESIONALES = [
    {
        "email": "juan@agendame.com",
        "nombre": "Juan",
        "apellido": "Pérez",
        "bio": "Cortes clásicos y modernos.",
        "dias": LUN_SAB,
        "horario": (time(9, 0), time(18, 0)),
        "servicios": [("Corte", 30, 800000), ("Corte y barba", 60, 1300000)],
    },
    {
        "email": "maria@agendame.com",
        "nombre": "María",
        "apellido": "Gómez",
        "bio": "Colorimetría y peinados.",
        "dias": LUN_VIE,
        "horario": (time(10, 0), time(19, 0)),
        "servicios": [("Brushing", 30, 900000), ("Color", 90, 2500000)],
    },
]


async def get_or_create_user(session: AsyncSession, email: str, password: str, nombre: str, rol: UserRole) -> User:
    repo = UserRepo(session)
    user = await repo.get_by_email(email)
    if user is None:
        user = await repo.create(email=email, password=password, nombre=nombre, rol=rol)
        print(f"  + usuario {email}")
    return user


# (día de la semana 0=lunes, hora, minuto, email cliente, índice de servicio, estado)
TURNOS_JUAN = [
    (0, 9, 0, "ana@agendame.com", 0, TurnoEstado.FINALIZADO),
    (0, 15, 0, "beto@agendame.com", 1, TurnoEstado.NO_ASISTIO),
    (1, 9, 0, "ana@agendame.com", 0, TurnoEstado.CONFIRMADO),
    (1, 15, 0, "beto@agendame.com", 1, TurnoEstado.CONFIRMADO),
    (2, 9, 30, "cliente@agendame.com", 0, TurnoEstado.CONFIRMADO),
    (2, 12, 0, "ana@agendame.com", 1, TurnoEstado.CONFIRMADO),
    (3, 16, 0, "beto@agendame.com", 0, TurnoEstado.CONFIRMADO),
    (4, 10, 0, "ana@agendame.com", 1, TurnoEstado.CANCELADO_CLIENTE),
]


async def seed_turnos_juan(session: AsyncSession) -> None:
    juan_user = await UserRepo(session).get_by_email("juan@agendame.com")
    if juan_user is None:
        return
    juan = await session.scalar(select(Profesional).where(Profesional.user_id == juan_user.id))
    if juan is None:
        return
    hoy = ahora_negocio().date()
    lunes = hoy - timedelta(days=hoy.weekday())
    desde = datetime.combine(lunes, time.min, tzinfo=UTC)
    hasta = desde + timedelta(days=7)
    existentes = list(
        await session.scalars(
            select(Turno).where(
                Turno.profesional_id == juan.id, Turno.fecha_inicio >= desde, Turno.fecha_inicio < hasta
            )
        )
    )
    if any(t.creado_por == "seed" for t in existentes):
        return  # ya sembrado esta semana
    servicios = sorted(juan.servicios, key=lambda s: s.orden)
    for dia, h, m, email, i_serv, estado in TURNOS_JUAN:
        user = await UserRepo(session).get_by_email(email)
        cliente = await session.scalar(select(Cliente).where(Cliente.user_id == user.id)) if user else None
        if cliente is None:
            continue
        servicio = servicios[i_serv]
        inicio = datetime.combine(lunes + timedelta(days=dia), time(h, m), tzinfo=UTC)
        fin = inicio + timedelta(minutes=servicio.duracion_min)
        ocupado = any(
            inicio < t.fecha_fin.replace(tzinfo=UTC) and fin > t.fecha_inicio.replace(tzinfo=UTC)
            for t in existentes
            if t.estado not in (TurnoEstado.CANCELADO_CLIENTE, TurnoEstado.CANCELADO_PROFESIONAL)
        )
        if ocupado:
            continue
        turno = Turno(
            profesional_id=juan.id,
            cliente_id=cliente.id,
            servicio_id=servicio.id,
            fecha_inicio=inicio,
            fecha_fin=fin,
            estado=estado,
            creado_por="seed",
        )
        session.add(turno)
        existentes.append(turno)
        print(f"  + turno {inicio:%a %d/%m %H:%M} {email} ({estado.value})")


async def seed() -> None:
    await init_db()
    async with async_session_maker() as session:
        await get_or_create_user(session, "admin@agendame.com", "Admin12345", "Admin", UserRole.ADMIN)
        await get_or_create_user(session, "cliente@agendame.com", "Cliente12345", "Cliente Demo", UserRole.CLIENTE)

        for data in PROFESIONALES:
            user = await get_or_create_user(
                session, data["email"], "Prof12345", str(data["nombre"]), UserRole.PROVEEDOR
            )
            prof = await session.scalar(select(Profesional).where(Profesional.user_id == user.id))
            if prof is None:
                prof = Profesional(
                    user_id=user.id,
                    nombre=data["nombre"],
                    apellido=data["apellido"],
                    bio=data["bio"],
                    slot_duracion_min=30,
                )
                session.add(prof)
                await session.flush()
                inicio, fin = data["horario"]  # type: ignore[misc]
                for dia in data["dias"]:  # type: ignore[attr-defined]
                    session.add(Disponibilidad(profesional_id=prof.id, dia_semana=dia, hora_inicio=inicio, hora_fin=fin))
                for orden, (nombre, duracion, precio) in enumerate(data["servicios"]):  # type: ignore[arg-type]
                    session.add(
                        Servicio(
                            profesional_id=prof.id, nombre=nombre, duracion_min=duracion, precio=precio, orden=orden
                        )
                    )
                print(f"  + profesional {data['nombre']} {data['apellido']}")

        await get_or_create_user(session, "ana@agendame.com", "Cliente12345", "Ana López", UserRole.CLIENTE)
        await get_or_create_user(session, "beto@agendame.com", "Cliente12345", "Beto Ruiz", UserRole.CLIENTE)
        await session.flush()
        await seed_turnos_juan(session)

        # Backfill: usuarios CLIENTE sin perfil Cliente
        sin_perfil = await session.scalars(
            select(User).outerjoin(Cliente, Cliente.user_id == User.id).where(
                User.rol == UserRole.CLIENTE, Cliente.id.is_(None)
            )
        )
        for user in sin_perfil.all():
            session.add(Cliente(user_id=user.id))
            print(f"  + perfil cliente para {user.email}")

        await session.commit()
    print("Seed OK")


if __name__ == "__main__":
    asyncio.run(seed())
