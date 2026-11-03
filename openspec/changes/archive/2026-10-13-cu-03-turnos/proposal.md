# Proposal

## Why

Implementar la gestión completa de turnos y reservas (CU-03 a CU-09) basada en la especificación existente en `openspec/specs/turnos/spec.md`. Los casos de uso CU-01 (Auth) y CU-02 (Profesionales) ya están implementados; ahora se requiere el core del negocio: disponibilidad, reservas, cancelaciones, reasignaciones e historial.

## What Changes

- **Nuevos endpoints API** bajo `/api/v1/turnos` y `/api/v1/profesionales/me/turnos` para CRUD de turnos y consultas de disponibilidad
- **Modelos SQLAlchemy**: `Turno`, `Cliente` (ya definido en spec), migraciones Alembic
- **Servicios**: `TurnoService` con lógica de negocio (validación de slots, transiciones de estado, reglas de cancelación/reasignación)
- **Repositorios**: `TurnoRepo` con queries optimizadas (disponibilidad, grilla profesional, historial)
- **Endpoints interno** para integración con Chatbot (CU-06)
- **Tests**: Unitarios para servicios/repos, integración para endpoints

## Capabilities

### New Capabilities
- Ninguna (la capacidad `turnos` ya existe en specs principales)

### Modified Capabilities
- `turnos`: Implementación completa de los requisitos funcionales RF-TURNO-01 a RF-TURNO-07, modelo de datos, endpoints API, flujo de estados y reglas de negocio definidos en la spec existente.

## Impact

### Código afectado (backend)
- `backend/app/models/turno.py` (nuevo)
- `backend/app/models/cliente.py` (nuevo o extendido)
- `backend/app/schemas/turno.py` (nuevo - Pydantic schemas)
- `backend/app/services/turno_service.py` (nuevo)
- `backend/app/repositories/turno_repo.py` (nuevo)
- `backend/app/api/v1/turnos.py` (nuevo - endpoints cliente)
- `backend/app/api/v1/profesionales.py` (extender - endpoints profesional)
- `backend/app/api/deps.py` (extender - dependencias de auth/roles)
- `backend/alembic/versions/` (nuevas migraciones)

### Frontend (futuro, fuera de este cambio)
- Páginas de disponibilidad, reserva, historial (cliente)
- Grilla de turnos, gestión de estados (profesional)
- Integración con chatbot (CU-06)

### Dependencias
- Requiere `cu-01-auth` (JWT, roles CLIENTE/PROVEEDOR/ADMIN)
- Requiere `cu-02-profesionales` (Profesional, Servicio, Disponibilidad modelos y repos)
- Usa `GROQ_API_KEY` solo en chatbot (CU-06, endpoint interno)