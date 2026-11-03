# Design

## Context

Ver [proposal.md](./proposal.md) para la motivación completa. Resumen del estado actual:

- **CU-01 Auth completado**: JWT HS256 (access 24h + refresh 7d rotativo), RBAC (CLIENTE/PROVEEDOR/ADMIN), rate limiting, RFC 7807 errors, migración Alembic base.
- **Specs principales existentes**: `openspec/specs/profesionales/` (completo, ver [spec.md](../openspec/specs/profesionales/spec.md)) y `openspec/specs/turnos/` (completo).
- **CU-02 objetivo**: Implementar capa backend completa para `profesionales`, `servicios`, `disponibilidad`, `excepciones_disponibilidad` + generación de slots.

Stack: FastAPI + SQLAlchemy 2.0 async + SQLite + Pydantic v2 + Alembic + pytest.

Arquitectura: Controllers (`api/v1/`) → Services (`services/`) → Repositories (`repositories/`) con DI via FastAPI `Depends`.

## Goals / Non-Goals

### Goals

- Implementar Models, Repositories, Services, API endpoints para: Profesional, Servicio, Disponibilidad, ExcepcionDisponibilidad
- Generación de slots disponibles (core business logic) con grilla semanal + excepciones + turnos existentes
- RBAC completo: Admin (total), Profesional (solo propio), Público (lectura)
- Migración Alembic reproducible + Tests ≥80% coverage (services)
- Código tipado (mypy strict), validado (ruff), documentado (OpenAPI)

### Non-Goals

- **Frontend** (CU-08): páginas, componentes, calendario visual
- **Chatbot IA** (CU-09): consulta de slots por lenguaje natural
- **Turnos/Reservas** (CU-03): ciclo de vida de turnos
- **Notificaciones** (CU-06): email/push
- **Admin Reportes** (CU-07): métricas/analytics

## Decisions

### 1. Modelos SQLAlchemy y Relaciones

**Decisión**: Usar modelos separados por entidad con FK explícitas y cascada configurada por relación.

```python
# Profesional ← User (1:1, FK en profesionales.usuario_id, unique=True)
# Profesional → Servicio (1:N, cascade="all, delete-orphan")
# Profesional → Disponibilidad (1:N, cascade="all, delete-orphan")
# Profesional → ExcepcionDisponibilidad (1:N, cascade="all, delete-orphan")
# Profesional → Turno (1:N, NO cascade - turnos son inmutables tras FINALIZADO)
```

**Racional**: 
- Separación clara de responsabilidades, testeable, migraciones limpias
- Cascada en hijos propios (servicios, disponibilidad, excepciones) evita huérfanos
- Turnos NO en cascada: son registros históricos inmutables

**Alternativas**: 
- Single table inheritance (rechazado: profesionales y clientes tienen campos muy distintos)
- FK en User → Profesional (rechazado: User es genérico, Profesional es perfil específico)

### 2. Generación de Slots: Algoritmo Determinístico

**Decisión**: Función pura `generar_slots(profesional_id, desde, hasta)` que:
1. Expande grilla semanal a rango de fechas
2. Aplica excepciones (prioridad absoluta)
3. Genera slots base cada `slot_duracion_min` (default 30, configurable)
4. Filtra slots ocupados por turnos CONFIRMADO/PENDIENTE/EN_CURSO
5. Retorna lista ordenada `{fecha, hora_inicio, hora_fin, disponible}`

**Racional**: 
- Función pura = testeable, determinística, paralelizable
- `slot_duracion_min` configurable por profesional (default 30) reemplaza MCM automático
- Excepciones tienen prioridad absoluta (simplifica lógica)

**Alternativas**: 
- MCM automático de duraciones de servicios (rechazado: genera slots muy finos, confusión UX)
- Generación on-demand por cada request (rechazado: performance, inconsistencia)

### 3. API Layer: Separación por Audiencia (RBAC en Router)

**Decisión**: Tres routers separados montados en paths distintos:

| Router | Prefijo | Audiencia | Auth |
|--------|---------|-----------|------|
| `profesionales_admin_router` | `/admin/profesionales` | ADMIN | `require_roles(ADMIN)` |
| `profesionales_me_router` | `/profesionales/me` | PROVEEDOR | `require_roles(PROVEEDOR)` |
| `profesionales_public_router` | `/profesionales` | Público/CLIENTE | Opcional |

**Racional**: 
- Separación clara de responsabilidades y permisos
- OpenAPI docs claras por audiencia
- Fácil testing y mantenimiento

**Alternativas**: 
- Un solo router con `require_roles` en cada endpoint (rechazado: mezcla responsabilidades, OpenAPI confuso)

### 4. Validación de Disponibilidad: Slot vs Turno

**Decisión**: Un slot está "disponible" si NO hay turno en estado CONFIRMADO, PENDIENTE o EN_CURSO solapado.

Estados que bloquean slot: `CONFIRMADO`, `PENDIENTE`, `EN_CURSO`
Estados que NO bloquean: `FINALIZADO`, `CANCELADO_*`, `NO_ASISTIO`

**Racional**: 
- Simple, consistente con flujo de estados de turnos
- `EN_CURSO` bloquea para evitar double-booking durante el turno

### 5. Paginación y Filtros: Estándar Unificado

**Decisión**: Todos los listados usan `PageParams(page=1, size=20, max_size=100)` + filtros via `FilterParams` genérico.

Response estándar:
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

### 6. Migración Alembic: Orden de Tablas

**Decisión**: Una sola migración con orden topológico:
1. `profesionales` (FK a users)
2. `servicios` (FK a profesionales)
3. `disponibilidades` (FK a profesionales)
4. `excepciones_disponibilidad` (FK a profesionales)
5. Índices compuestos para consultas frecuentes

### 7. Testing Strategy

| Capa | Enfoque | Cobertura objetivo |
|------|---------|-------------------|
| Models | Unit (factory + BD real) | 100% constraints |
| Repositories | Unit (mock session) + Integration (BD real) | 90% |
| Services | Unit (mock repo) | ≥85% |
| API Endpoints | Integration (AsyncClient + BD real) | 80% |
| Slots Logic | Unit (función pura) | 100% edge cases |

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| **Slots generation performance** en rangos grandes (>30 días) | Limitar rango máximo a 60 días; paginar resultados; cache opcional futuro |
| **Race condition** al reservar último slot | Transacción BD con `SELECT ... FOR UPDATE` en check+insert turno |
| **Excepciones complejas** (parciales, recurrentes) | MVP: solo excepciones puntuales por fecha; recurrentes en CU futuro |
| **Slot_duracion_min muy pequeño** (< 10 min) genera miles de slots | Validar `slot_duracion_min >= 10` y `>= min(duracion_servicios)` |
| **Profesional con muchos servicios** → slots muy fragmentados | Validar `slot_duracion_min >= min(duracion_servicios)` o sugerir MCM en UI |

## Migration Plan

```bash
# 1. Generar migración
cd backend && alembic revision --autogenerate -m "profesionales_servicios_disponibilidad"

# 2. Revisar migración generada (orden FK, índices, constraints)

# 3. Aplicar
alembic upgrade head

# 4. Verificar
sqlite3 agendame.db ".schema profesionales"
sqlite3 agendame.db ".schema servicios"
sqlite3 agendame.db ".schema disponibilidades"
sqlite3 agendame.db ".schema excepciones_disponibilidad"

# 5. Tests
pytest -v --cov=app --cov-fail-under=80

# Rollback si falla:
alembic downgrade -1
```

## Open Questions

1. **¿Soft delete real o hard delete para profesional?** → MVP: soft delete (`activo=false`) + validación turnos futuros. Hard delete solo admin vía DB directa.

2. **¿Validar `slot_duracion_min >= min(duracion_servicios)` en BD o solo API?** → API + check constraint en BD para integridad.

3. **¿Cache de slots?** → No en MVP. Evaluar Redis en CU-09 (chatbot) si performance lo requiere.

4. **¿Endpoints públicos `/profesionales/{id}/slots` requieren auth?** → No (lectura pública), pero rate limiting estricto.

5. **¿Validar `slot_duracion_min` multiplo de duraciones de servicios?** → Solo warning en API, no bloquear. Frontend sugiere MCM.