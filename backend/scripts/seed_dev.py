"""Datos de prueba para desarrollo (idempotente).

Uso (desde backend/):
    python scripts/seed_dev.py

Credenciales de prueba (solo desarrollo local):
    admin@agendame.com    / Admin12345   (ADMIN)
    juan@agendame.com     / Prof12345    (PROVEEDOR) - Juan Pérez, lun-sáb 09:00-18:00
    maria@agendame.com    / Prof12345    (PROVEEDOR) - María Gómez, lun-vie 10:00-19:00
    cliente@agendame.com  / Cliente12345 (CLIENTE)

Además crea el perfil Cliente que falte a usuarios CLIENTE registrados antes
de que el registro lo creara automáticamente.
"""

import asyncio
import sys
from datetime import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.database import async_session_maker, init_db  # noqa: E402
from app.models.cliente import Cliente  # noqa: E402
from app.models.profesional import DiaSemana, Disponibilidad, Profesional, Servicio  # noqa: E402
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
