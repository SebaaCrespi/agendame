# Tasks

## 1. Setup del Proyecto Backend

- [x] 1.1 Crear estructura de directorios `backend/app/{api,core,models,schemas,services,repositories}` y `__init__.py` en cada uno; verificar con `ls -la backend/app/`
- [x] 1.2 Crear `backend/requirements.txt` con dependencias: fastapi, uvicorn[standard], sqlalchemy[asyncio], aiosqlite, alembic, pydantic, pydantic-settings, python-jose[cryptography], passlib[bcrypt], python-multipart, httpx, pytest, pytest-asyncio, pytest-cov, ruff, mypy, slowapi, python-dotenv, email-validator; verificar `pip install -r backend/requirements.txt`
- [x] 1.3 Crear `backend/pyproject.toml` con configuración mypy (strict), ruff, pytest; verificar `mypy --version`, `ruff --version`
- [x] 1.4 Crear `backend/.env.example` con todas las variables requeridas (ver spec system); verificar archivo existe
- [x] 1.5 Crear `backend/alembic.ini` y directorio `alembic/` con `env.py` async configurado para SQLite; verificar `alembic current` sin errores

## 2. Core: Config, Database, Security, Error Handling

- [x] 2.1 Implementar `backend/app/core/config.py` con clase `Settings` (Pydantic Settings v2) cargando .env; verificar `python -c "from app.core.config import settings; print(settings.DATABASE_URL)"`
- [x] 2.2 Implementar `backend/app/core/database.py` con `async_engine`, `async_sessionmaker`, `get_db` dependency, `Base` declarativa; verificar `python -c "from app.core.database import Base; print(Base.metadata.tables.keys())"`
- [x] 2.3 Implementar `backend/app/core/security.py` con `pwd_context` (bcrypt 12), `create_access_token`, `create_refresh_token`, `verify_token`, `decode_token`; verificar test unitario hash/verify password y create/decode JWT
- [x] 2.4 Implementar `backend/app/core/exceptions.py` con `AppException`, `ProblemDetail` (RFC 7807), exception handlers globales; verificar `pytest tests/test_exceptions.py -v`
- [x] 2.5 Implementar `backend/app/core/__init__.py` exportando símbolos públicos; verificar imports funcionan

## 3. Modelos y Migración Inicial

- [x] 3.1 Implementar `backend/app/models/user.py` con `User`, `UserRole` enum, `RefreshToken` modelo; relaciones a Profesional/Cliente (string forward refs); verificar `python -c "from app.models.user import User, UserRole; print(User.__tablename__)"`
- [x] 3.2 Generar migración inicial: `cd backend && alembic revision --autogenerate -m "initial"`; verificar archivo generado en `alembic/versions/`
- [x] 3.3 Aplicar migración: `cd backend && alembic upgrade head`; verificar `sqlite3 agendame.db ".schema users"`

## 4. Esquemas Pydantic (Request/Response)

- [x] 4.1 Implementar `backend/app/schemas/auth.py`: `UserRegister`, `UserLogin`, `TokenResponse`, `TokenRefresh`, `UserResponse`, `UserUpdate`; verificar validaciones Pydantic (email, password min 8, rol enum)
- [x] 4.2 Implementar `backend/app/schemas/__init__.py` exportando schemas; verificar imports

## 5. Repositorios (Data Access)

- [x] 5.1 Implementar `backend/app/repositories/user_repo.py` con `UserRepo`: `create`, `get_by_id`, `get_by_email`, `update`, `create_refresh_token`, `get_valid_refresh_token`, `revoke_refresh_token`, `revoke_all_user_tokens`; verificar con tests unitarios mock DB
- [x] 5.2 Implementar `backend/app/repositories/__init__.py`; verificar imports

## 6. Servicios (Business Logic)

- [x] 6.1 Implementar `backend/app/services/auth_service.py` con `AuthService`: `register`, `login`, `refresh_tokens`, `get_current_user`, `update_profile`; lógica de validación, hash, tokens, rotación refresh; verificar tests unitarios con mock repo (≥80% coverage)
- [x] 6.2 Implementar `backend/app/services/__init__.py`; verificar imports

## 7. Dependencias de Autenticación y RBAC

- [x] 7.1 Implementar `backend/app/api/deps.py`: `get_current_user`, `require_roles(*roles)`, `get_current_profesional` (placeholder), `get_current_cliente` (placeholder), rate limiter `limiter`; verificar imports y tipado
- [x] 7.2 Tests de integración para deps: `pytest tests/test_deps.py -v` (mock JWT válido/inválido/expirado, roles)

## 8. Endpoints API (Controllers)

- [x] 8.1 Implementar `backend/app/api/v1/auth.py` con router `auth_router`: `POST /register`, `POST /login`, `POST /refresh`, `GET /me`, `PUT /me`; usar `AuthService` via dependency, `require_roles` donde corresponda; rate limit en register/login
- [x] 8.2 Implementar `backend/app/api/v1/__init__.py` exportando routers; verificar imports
- [x] 8.3 Tests de integración endpoints: `pytest tests/api/v1/test_auth.py -v` (register, login, refresh, me, update, errores 401/403/409/422/429)

## 9. App Factory y Health Check

- [x] 9.1 Implementar `backend/app/main.py`: `create_app()` con lifespan, CORS, routers `/api/v1`, exception handlers, health check `/health`; verificar `uvicorn app.main:app --reload` arranca
- [x] 9.2 Tests de integración app: `pytest tests/test_main.py -v` (health, CORS, docs en /docs)

## 10. Configuración de Testing y Calidad

- [x] 10.1 Crear `backend/tests/conftest.py` con fixtures: `async_client`, `db_session`, `test_user`, `auth_headers`, `profesional_user`, `admin_user`; verificar `pytest --collect-only`
- [x] 10.2 Configurar `backend/pytest.ini` con `asyncio_mode = auto`, `testpaths = tests`; verificar `pytest -v`
- [x] 10.3 Ejecutar suite completa: `cd backend && pytest --cov=app --cov-report=term-missing --cov-fail-under=80`; verificar coverage ≥ 80%
- [x] 10.4 Ejecutar lint y typecheck: `cd backend && ruff check app/` y `mypy app/`; verificar sin errores

## 11. Verificación End-to-End

- [x] 11.1 Probar flujo completo manual: register → login → access /me → refresh → access /me con nuevo token; verificar con curl o httpie
- [x] 11.2 Probar RBAC: crear usuario ADMIN, PROVEEDOR, CLIENTE; verificar accesos permitidos/denegados según spec
- [x] 11.3 Probar rate limiting: 6 requests seguidos a /login → 429; verificar
- [x] 11.4 Verificar migración limpia: `alembic downgrade base && alembic upgrade head` sin errores

## Workflow follow-up

- Ejecutar `/opsx-archive` para archivar este cambio tras verificación exitosa
- Ejecutar `/learn "CU-01 auth implementado: estructura backend, JWT HS256 access+refresh rotativo, RBAC, tests ≥80%, migración Alembic"` para guardar en Engram