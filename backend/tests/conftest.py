"""Pytest configuration and shared fixtures for Agendame backend tests.

Each test gets its own fresh SQLite file database, so tests never leak data
between each other.
"""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.deps import limiter
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, create_refresh_token, hash_token
from app.main import create_app
from app.models.cliente import Cliente
from app.models.profesional import DiaSemana, Disponibilidad, Profesional, Servicio
from app.models.turno import Turno, TurnoEstado
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepo
from app.services.auth_service import AuthService


def unique_email(prefix: str = "user") -> str:
    """Return a valid, unique email address."""
    return f"{prefix}_{uuid.uuid4().hex[:10]}@test.com"


def headers_for(user: User) -> dict[str, str]:
    """Build Bearer auth headers for a user."""
    token = create_access_token({"sub": str(user.id), "rol": user.rol.value})
    return {"Authorization": f"Bearer {token}"}


def proximo_dia_habil(dias: int = 1) -> date:
    """Return a date `dias` days from today (always in the future)."""
    return date.today() + timedelta(days=dias)


# =============================================================================
# Database
# =============================================================================


@pytest.fixture
async def test_engine(tmp_path: Path):
    """Fresh SQLite database per test."""
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        poolclass=NullPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(test_engine) -> async_sessionmaker[AsyncSession]:
    """Session factory bound to the per-test database."""
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


@pytest.fixture
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Database session shared by fixtures and the test client."""
    async with session_factory() as session:
        yield session
        await session.rollback()


# =============================================================================
# HTTP client
# =============================================================================


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Start each test with empty rate-limit counters."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client against the real app, using the test database session."""
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def isolated_app(session_factory):
    """App where every request opens its own DB session (like production)."""
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    return app


# =============================================================================
# Users (auth)
# =============================================================================


@pytest.fixture
def test_user_data() -> dict:
    return {
        "email": unique_email("cliente"),
        "password": "testpassword123",
        "nombre": "Test User",
        "rol": "CLIENTE",
    }


@pytest.fixture
async def test_user(db_session: AsyncSession, test_user_data: dict) -> User:
    """CLIENTE user (with its Cliente profile)."""
    user = await UserRepo(db_session).create(
        email=test_user_data["email"],
        password=test_user_data["password"],
        nombre=test_user_data["nombre"],
        rol=UserRole(test_user_data["rol"]),
    )
    await db_session.commit()
    return user


@pytest.fixture
async def test_profesional(db_session: AsyncSession) -> User:
    """PROVEEDOR user without profesional profile."""
    user = await UserRepo(db_session).create(
        email=unique_email("proveedor"),
        password="profepassword123",
        nombre="Profesional Test",
        rol=UserRole.PROVEEDOR,
    )
    await db_session.commit()
    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    user = await UserRepo(db_session).create(
        email=unique_email("admin"),
        password="adminpassword123",
        nombre="Admin Test",
        rol=UserRole.ADMIN,
    )
    await db_session.commit()
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    return headers_for(test_user)


@pytest.fixture
def profesional_headers(test_profesional: User) -> dict:
    return headers_for(test_profesional)


@pytest.fixture
def admin_headers(test_admin: User) -> dict:
    return headers_for(test_admin)


@pytest.fixture
async def test_refresh_token(db_session: AsyncSession, test_user: User) -> str:
    refresh_token = create_refresh_token({"sub": str(test_user.id)})
    await UserRepo(db_session).create_refresh_token(
        user_id=test_user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    await db_session.commit()
    return refresh_token


@pytest.fixture
async def auth_service(db_session: AsyncSession) -> AuthService:
    return AuthService(db_session)


@pytest.fixture
async def user_repo(db_session: AsyncSession) -> UserRepo:
    return UserRepo(db_session)


# =============================================================================
# Domain: cliente, profesional, servicio, turnos
# =============================================================================


@pytest.fixture
async def sample_cliente(test_user: User, db_session: AsyncSession) -> Cliente:
    """Cliente profile of `test_user`."""
    await db_session.refresh(test_user, ["cliente"])
    assert test_user.cliente is not None
    return test_user.cliente


ProfesionalFactory = Callable[..., Awaitable[Profesional]]


@pytest.fixture
def make_profesional(db_session: AsyncSession) -> ProfesionalFactory:
    """Create a PROVEEDOR user + profesional with availability every day 09:00-18:00."""

    async def _make(nombre: str = "Juan", apellido: str = "Perez", activo: bool = True) -> Profesional:
        user = await UserRepo(db_session).create(
            email=unique_email("prof"),
            password="profepassword123",
            nombre=nombre,
            rol=UserRole.PROVEEDOR,
        )
        prof = Profesional(user_id=user.id, nombre=nombre, apellido=apellido, activo=activo, slot_duracion_min=30)
        db_session.add(prof)
        await db_session.flush()
        for dia in DiaSemana:
            db_session.add(
                Disponibilidad(
                    profesional_id=prof.id, dia_semana=dia, hora_inicio=time(9, 0), hora_fin=time(18, 0)
                )
            )
        await db_session.commit()
        await db_session.refresh(prof)
        return prof

    return _make


@pytest.fixture
async def sample_profesional(make_profesional: ProfesionalFactory) -> Profesional:
    return await make_profesional()


@pytest.fixture
async def sample_servicio(db_session: AsyncSession, sample_profesional: Profesional) -> Servicio:
    servicio = Servicio(
        profesional_id=sample_profesional.id, nombre="Corte", duracion_min=30, precio=500000
    )
    db_session.add(servicio)
    await db_session.commit()
    await db_session.refresh(servicio)
    # la sesión de tests es compartida: refrescar la relación cacheada
    await db_session.refresh(sample_profesional, ["servicios"])
    return servicio


@pytest.fixture
async def servicio_largo(db_session: AsyncSession, sample_profesional: Profesional) -> Servicio:
    """Servicio de 60 min (2 slots de 30) del profesional de ejemplo."""
    servicio = Servicio(
        profesional_id=sample_profesional.id, nombre="Color", duracion_min=60, precio=1500000
    )
    db_session.add(servicio)
    await db_session.commit()
    await db_session.refresh(servicio)
    # la sesión de tests es compartida: refrescar la relación cacheada
    await db_session.refresh(sample_profesional, ["servicios"])
    return servicio


@pytest.fixture
async def proveedor_headers(db_session: AsyncSession, sample_profesional: Profesional) -> dict:
    user = await db_session.get(User, sample_profesional.user_id)
    assert user is not None
    return headers_for(user)


TurnoFactory = Callable[..., Awaitable[Turno]]


@pytest.fixture
def make_turno(db_session: AsyncSession) -> TurnoFactory:
    """Insert a turno directly in the DB."""

    async def _make(
        cliente: Cliente,
        profesional: Profesional,
        servicio: Servicio,
        inicio: datetime | None = None,
        estado: TurnoEstado = TurnoEstado.CONFIRMADO,
    ) -> Turno:
        inicio = inicio or datetime.combine(proximo_dia_habil(3), time(10, 0), tzinfo=UTC)
        turno = Turno(
            profesional_id=profesional.id,
            cliente_id=cliente.id,
            servicio_id=servicio.id,
            fecha_inicio=inicio,
            fecha_fin=inicio + timedelta(minutes=servicio.duracion_min),
            estado=estado,
            creado_por="cliente",
        )
        db_session.add(turno)
        await db_session.commit()
        await db_session.refresh(turno)
        return turno

    return _make


@pytest.fixture
async def sample_turno(
    make_turno: TurnoFactory, sample_cliente: Cliente, sample_profesional: Profesional, sample_servicio: Servicio
) -> Turno:
    return await make_turno(sample_cliente, sample_profesional, sample_servicio)


@pytest.fixture
def api_key_header() -> dict[str, str]:
    return {"X-Internal-API-Key": settings.INTERNAL_API_KEY}


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
