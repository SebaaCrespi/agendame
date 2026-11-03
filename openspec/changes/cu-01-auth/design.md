# Design

## Context

Proyecto greenfield: no existe código backend previo. La especificación de auth (openspec/specs/auth/spec.md) define 5 requisitos funcionales (RF-AUTH-01 a RF-AUTH-05) que cubren registro, login, refresh, middleware JWT y RBAC. El dominio `system` provee la infraestructura base (config, DB, security, error handling, app factory).

Stack definido: FastAPI + SQLAlchemy 2.0 (async) + SQLite + Alembic + Pydantic v2 + python-jose + passlib[bcrypt].

Arquitectura objetivo: Controllers (api/v1/) → Services (services/) → Repositories (repositories/) con inyección de dependencias via FastAPI Depends.

## Goals / Non-Goals

**Goals:**
- Implementar auth completo según spec: register, login, refresh, middleware, RBAC
- Establecer estructura base del proyecto (config, database, security, main, health)
- Código tipado (mypy strict), validado (ruff), testeado (pytest ≥80% services)
- Migración Alembic inicial reproducible
- Separación estricta de capas (Controller/Service/Repository)

**Non-Goals:**
- Frontend (páginas login/registro)
- Recuperación de contraseña, verificación email
- OAuth2 / social login
- Rate limiting distribuido (Redis) — solo in-memory
- Auditoría de seguridad avanzada (logs de acceso, etc.)

## Decisions

### 1. Estructura de paquetes y capas
**Decisión**: Usar `backend/app/` con subpaquetes `api/`, `core/`, `models/`, `schemas/`, `services/`, `repositories/`.

**Racional**: Alineado con AGENTS.md y Clean Architecture. Separación clara de responsabilidades, testeable, escalable.

**Alternativas**: Flat structure (rechazado: no escala), Domain-driven packages (rechazado: prematuro para CU-01).

### 2. SQLAlchemy Async + SQLite
**Decisión**: `sqlite+aiosqlite` con `AsyncSession`, `async_engine`, `async_sessionmaker`.

**Racional**: FastAPI nativo async, SQLite para dev simple, migración fácil a PostgreSQL cambiando URL.

**Alternativas**: Sync SQLAlchemy (rechazado: bloquea event loop), PostgreSQL desde inicio (rechazado: complejidad dev).

### 3. Autenticación: JWT HS256 con Access + Refresh Rotativo
**Decisión**: 
- Access token: 24h, claim `sub=user_id`, `rol=role`
- Refresh token: 7d, claim `sub=user_id`, `type=refresh`, almacenado en BD (hash) para rotación e invalidación
- Rotación: cada refresh invalida el anterior y genera par nuevo
- Almacenamiento refresh: tabla `refresh_tokens` (user_id, token_hash, expires_at, revoked_at)

**Racional**: Seguridad (rotación previene replay), stateless access, revocación real de refresh tokens.

**Alternativas**: Solo access token largo (rechazado: riesgo seguridad), Refresh en cookie HttpOnly (rechazado: CORS complejidad, frontend separado).

### 4. Password Hashing: bcrypt cost 12
**Decisión**: `passlib.context.CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)`.

**Racional**: Estándar industria, coste configurable, resistente a GPU.

### 5. Rate Limiting: In-memory (slowapi)
**Decisión**: `slowapi` con `Limiter(key_func=get_remote_address)` en login/register (5 req/min).

**Racional**: Simple, sin dependencias externas, suficiente para MVP.

**Alternativas**: Redis (rechazado: infra extra), middleware custom (rechazado: reinventar rueda).

### 6. Manejo de Errores: RFC 7807 + Exception Handlers
**Decisión**: Clase `AppException(status_code, detail, type)` + handlers globales que retornan `ProblemDetail` (RFC 7807).

**Racional**: Estándar interoperable, frontend puede parsear uniformemente, extensible.

### 7. Configuración: Pydantic Settings v2
**Decisión**: `Settings` class en `core/config.py` con `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`.

**Racional**: Validación de tipos, valores por defecto seguros, documentación viva.

### 8. Migraciones: Alembic async
**Decisión**: `alembic.ini` configurado para `asyncpg`/`aiosqlite`, `env.py` usa `async_engine`, `run_migrations_online` async.

**Racional**: Compatible con SQLAlchemy 2.0 async, estándar de facto.

### 9. RBAC: Dependencias FastAPI reutilizables
**Decisión**: 
- `get_current_user` → extrae user de JWT, retorna `User` model
- `require_roles(*roles)` → dependency que verifica `current_user.rol in roles`
- `get_current_profesional` → dependency que verifica rol PROVEEDOR y carga `Profesional` asociado

**Racional**: Declarativo, reutilizable, tipado, integra con OpenAPI.

### 10. Testing: pytest + httpx.AsyncClient + fixtures
**Decisión**: 
- `conftest.py` con `async_client`, `db_session`, `test_user`, `auth_headers` fixtures
- Tests unitarios para services (mock repo), integración para endpoints (real DB)
- Coverage ≥ 80% en services

**Racional**: Estándar FastAPI, async nativo, aislamiento de tests via transacciones rollback.

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| SQLite locking en tests concurrentes | Usar `:memory:` o archivo temporal por test session, `poolclass=NullPool` |
| Refresh token rotation race condition | Transacción DB atómica: revocar old + crear new en misma sesión |
| JWT secret en .env commiteado | `.env.example` sin secret, `.gitignore` incluye `.env`, secret generado en deploy |
| Rate limiting in-memory no persiste entre workers | Documentar limitación; migración a Redis en CU posterior si scaling requerido |
| Circular imports (models ↔ repositories) | Importar models solo en TYPE_CHECKING, usar string annotations en relationships |
| Alembic async + SQLite limitaciones (ALTER TABLE) | Usar `batch_mode=True` en env.py para SQLite, aceptar limitaciones dev |

## Migration Plan

1. `pip install -r requirements.txt`
2. Crear `.env` desde `.env.example` con `JWT_SECRET_KEY` generado (`openssl rand -hex 32`)
3. `alembic upgrade head` → crea tablas iniciales
4. `uvicorn app.main:app --reload` → server en :8000
5. Verificar `/docs` y `/health`
6. Ejecutar `pytest -v` → todos pasan
7. `mypy app/` y `ruff check app/` → sin errores

**Rollback**: `alembic downgrade base` + borrar `agendame.db`

## Open Questions

1. **¿Frontend usará cookies HttpOnly o localStorage para tokens?**
   - Impacta CORS y design de refresh endpoint. Asumimos localStorage (Bearer header) por ahora; ajustable en CU-frontend.

2. **¿Se requiere logout explícito (invalidar refresh token)?**
   - Spec no lo menciona. Añadir endpoint `POST /auth/logout` que revoca refresh token actual es trivial; decidir en implementación.

3. **¿Validación de password policy más allá de longitud mínima?**
   - Spec dice "mínimo 8 chars". Podríamos añadir zxcvbn o regex; mantener simple v1.

4. **¿Campos extra en User (avatar, timezone, locale)?**
   - Spec no los requiere. Dejar para CU-02/10 (perfil profesional/cliente).