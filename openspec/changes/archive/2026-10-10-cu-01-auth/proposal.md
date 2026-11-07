# Proposal

## Why

CU-01 (Autenticación y Autorización) es la base del sistema Agendame. Sin autenticación no se pueden implementar los demás casos de uso (profesionales, turnos, chatbot) ya que todos requieren identificación de usuario y control de acceso por rol (CLIENTE, PROVEEDOR, ADMIN). Este cambio implementa el sistema completo de registro, login, JWT con refresh tokens rotativos y middleware RBAC.

## What Changes

- **Nuevo**: Backend FastAPI completo con arquitectura Controllers → Services → Repositories
- **Nuevo**: Modelos SQLAlchemy (User, roles, relaciones con Profesional/Cliente)
- **Nuevo**: Schemas Pydantic v2 para request/response (Register, Login, Token, UserResponse)
- **Nuevo**: Endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`, `PUT /auth/me`
- **Nuevo**: Seguridad: bcrypt (cost 12), JWT HS256 (access 24h + refresh 7d rotativo), rate limiting 5 req/min
- **Nuevo**: Middleware de autenticación + dependencias RBAC (`require_roles`, `get_current_user`)
- **Nuevo**: Tests unitarios e integración (pytest + httpx, coverage ≥ 80%)
- **Nuevo**: Migración Alembic inicial
- **Nuevo**: Configuración por variables de entorno (.env)

## Capabilities

### Modified Capabilities

- `auth`: Implementar los requisitos funcionales RF-AUTH-01 a RF-AUTH-05 definidos en `openspec/specs/auth/spec.md` (registro, login, refresh, middleware JWT, RBAC por roles)

### New Capabilities

- `system`: Configuración base del proyecto (config, database, security, main.py, health check) — requerida como fundación para auth y futuros dominios

## Impact

- **Código nuevo**: `backend/app/` completo (api, core, models, schemas, services, repositories, main)
- **APIs nuevas**: 5 endpoints bajo `/api/v1/auth/`
- **Dependencias**: fastapi, uvicorn, sqlalchemy, alembic, pydantic, python-jose, passlib, bcrypt, python-multipart, httpx, pytest
- **Base de datos**: Tabla `users` + enum `UserRole` + índices
- **Variables de entorno**: JWT_SECRET_KEY, DATABASE_URL, CORS_ORIGINS, etc.
- **Fuera de alcance**: Frontend (React), chatbot, profesionales, turnos — se harán en cambios posteriores

## Out of Scope

- Frontend (páginas de login/registro)
- Recuperación de contraseña / email verification
- OAuth2 / social login
- Auditoría de seguridad avanzada
- Rate limiting distribuido (Redis) — solo in-memory por ahora