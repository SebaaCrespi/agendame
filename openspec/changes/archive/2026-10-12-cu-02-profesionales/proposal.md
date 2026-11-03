# Proposal

## Why

CU-02 (Gestión de Profesionales y Servicios) es el dominio core del sistema Agendame. Sin profesionales, sus servicios y su disponibilidad, no se pueden implementar turnos (CU-03), chatbot (CU-09) ni notificaciones (CU-06). Este cambio implementa la capa backend completa para los specs ya definidos en `openspec/specs/profesionales/`.

## What Changes

- **Nuevo**: Backend completo para dominio `profesionales` y `servicios` (Models, Repositories, Services, API endpoints)
- **Nuevo**: Backend completo para dominio `disponibilidad` y `excepciones_disponibilidad` (grilla semanal + excepciones)
- **Nuevo**: Endpoints API con RBAC (Admin total, Profesional solo suyo, Público lectura)
- **Nuevo**: Generación de slots disponibles (lógica de negocio core)
- **Nuevo**: Migración Alembic para tablas: profesionales, servicios, disponibilidades, excepciones_disponibilidad
- **Nuevo**: Tests unitarios e integración (≥80% coverage en services)

## Capabilities

### New Capabilities

- `profesionales`: Gestión completa de profesionales (proveedores/peluqueros), sus servicios, disponibilidad horaria (grilla semanal + excepciones) y generación de slots disponibles. Implementa specs `openspec/specs/profesionales/` (CU-02, CU-10).

### Modified Capabilities

- `system`: Extensión de configuración base para soportar nuevos modelos y endpoints (ya existe en CU-01).

## Impact

- **Código nuevo**: `backend/app/models/profesional.py`, `servicio.py`, `disponibilidad.py`, `excepcion_disponibilidad.py` + repos, services, API v1
- **APIs nuevas**: 15+ endpoints bajo `/api/v1/profesionales/`, `/api/v1/admin/profesionales/`, `/api/v1/public/profesionales/`
- **Dependencias**: Requiere CU-01 (Auth, User, RBAC, UserRole.PROVEEDOR)
- **Base de datos**: 4 tablas nuevas + índices + constraints (FK a users, cascada en cascada)
- **Variables de entorno**: Ninguna nueva (usa JWT, DB, CORS existentes)

## Out of Scope

- **Frontend** (CU-08): Páginas de gestión profesional, calendario, formularios
- **Chatbot IA** (CU-09): Consulta de disponibilidad por lenguaje natural
- **Turnos/Reservas** (CU-03): Ciclo de vida de turnos (depende de slots)
- **Notificaciones** (CU-06): Email/push al crear/modificar profesional
- **Admin Reportes** (CU-07): Métricas de profesionales