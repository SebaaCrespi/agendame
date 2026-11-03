# Design

## Context

- **Propuesta**: Ver `proposal.md` - Why/What
- **Specs**: Ver `specs/turnos/spec.md` - Requisitos RF-TURNO-01 a RF-TURNO-07
- **Estado actual**: 
  - Models: `Turno` y `Cliente` existen como placeholders en `backend/app/models/`
  - Slot generation: `SlotService` + `SlotRepo` ya implementados (generan slots a partir de grilla/excepciones/turnos)
  - Profesionales/Servicios/Disponibilidad: Totalmente implementados (CU-02)
  - Auth: JWT con roles CLIENTE/PROVEEDOR/ADMIN (CU-01)
  - API público: Endpoints para listar profesionales, servicios, grilla, excepciones, slots

## Goals / Non-Goals

**Goals:**
- Implementar CRUD completo de Turnos siguiendo arquitectura Controllers → Services → Repositories
- Endpoints para Cliente (reserva, historial, cancelación) y Profesional (grilla, estados, reasignación, cancelación, notas)
- Endpoint interno para Chatbot (integración CU-06)
- Validaciones de negocio: unicidad de slot, transiciones de estado, reglas de cancelación/reasignación
- Migración Alembic para tablas `turnos` y `clientes`
- Tests unitarios (services/repos) e integración (endpoints)

**Non-Goals:**
- Notificaciones (email/WS) - CU-10
- Frontend - fuera de backend
- Chatbot LLM logic - CU-06 (solo endpoint interno)
- Admin dashboard endpoints - CU-09 (solo GET listado/filtrado básico)

## Decisions

### 1. Modelo de Datos: Turno y Cliente
**Decisión**: Completar modelos existentes `Turno` y `Cliente` según spec, usando `DateTime(timezone=True)` para timestamps.

**Rationale**: 
- El modelo `Turno` actual usa `fecha_inicio`/`fecha_fin` como `DateTime` (no `Date` + `Time` separados). Esto simplifica queries de solapamiento y timezone handling.
- `Cliente` separado de `User` permite datos específicos (teléfono, preferencias) y aislamiento.
- Enum `TurnoEstado` con valores en mayúsculas (coherente con código actual).

**Alternativas consideradas**:
- `Date` + `Time` separados (como en spec original): más complejo para queries de solapamiento, requiere combinar en aplicación.
- Un solo modelo `User` con rol: mezcla responsabilidades, Cliente tiene datos distintos.

### 2. Repositorio: TurnoRepo
**Decisión**: Nuevo `TurnoRepo` con queries específicas:
- `get_by_id(id)`
- `get_by_cliente(cliente_id, filtros)` - historial cliente
- `get_by_profesional(profesional_id, filtros)` - grilla profesional
- `get_turnos_ocupados(profesional_id, desde, hasta)` - para slot generation (ya usado por SlotRepo)
- `crear_turno(data)` - con validación de unicidad (lock DB)
- `actualizar_estado(turno_id, nuevo_estado, user_id, motivo?)`
- `reasignar(turno_id, nueva_fecha, nueva_hora, user_id, motivo)`
- `agregar_notas(turno_id, notas_profesional)`
- `cancelar(turno_id, cancelado_por, motivo, user_id)`

**Rationale**: Centraliza lógica de acceso a datos, permite optimizar queries con índices definidos en modelo.

### 3. Servicio: TurnoService
**Decisión**: `TurnoService` con métodos verbosos que encapsulan reglas de negocio:
- `consultar_disponibilidad(profesional_id?, servicio_id?, desde, hasta)` - usa SlotService internamente
- `crear_reserva_manual(cliente_id, profesional_id, servicio_id, fecha, hora)` - valida slot libre, servicio del prof, crea turno
- `cancelar_turno_cliente(turno_id, cliente_id, motivo)` - valida >2h, propio
- `cancelar_turno_profesional(turno_id, profesional_id, motivo)` - valida futuro, propio
- `cambiar_estado(turno_id, profesional_id, nuevo_estado)` - valida transición válida
- `reasignar_turno(turno_id, profesional_id, nueva_fecha, nueva_hora, motivo)` - valida slot libre, mismo servicio
- `agregar_notas_profesional(turno_id, profesional_id, notas)`
- `obtener_turno_para_chatbot(turno_id)` - interno
- `crear_turno_desde_chatbot(data)` - valida igual que manual, endpoint interno

**Rationale**: Separación clara - Service orquesta, Repo accede a DB. Transacciones en Service.

### 4. Endpoints API - Estructura
**Decisión**: Dos routers separados por audiencia:
- `turnos.py` (cliente): `/turnos/disponibilidad`, `POST /turnos`, `GET /turnos/mis-turnos`, `GET /turnos/{id}`, `PUT /turnos/{id}/cancelar`
- `profesionales_me.py` (extendido): `/profesionales/me/turnos`, `GET /profesionales/me/turnos/{id}`, `PUT /profesionales/me/turnos/{id}/estado`, `PUT /profesionales/me/turnos/{id}/reasignar`, `PUT /profesionales/me/turnos/{id}/cancelar`, `PUT /profesionales/me/turnos/{id}/notas`
- `chat.py` (interno): `POST /internal/turnos/reservar` (API key header)

**Rationale**: 
- Separación por roles = aislamiento de datos enforced en controller
- `/profesionales/me/turnos` reusa patrón existente en `profesionales_me.py`
- Endpoint interno con API key separada de JWT

### 5. Esquemas Pydantic (schemas/turno.py)
**Decisión**: Schemas separados por operación:
- `TurnoCreate` (cliente): profesional_id, servicio_id, fecha, hora_inicio
- `TurnoResponse`: id, cliente_id, profesional_id, servicio_id, fecha_inicio, fecha_fin, estado, notas_cliente, notas_profesional, creado_en, confirmado_en, finalizado_en, cancelado_en, cancelado_por, motivo_cancelacion
- `TurnoEstadoUpdate` (profesional): nuevo_estado (enum)
- `TurnoReasignar` (profesional): nueva_fecha, nueva_hora_inicio, motivo
- `TurnoCancelar` (cliente/profesional): motivo
- `TurnoNotasUpdate` (profesional): notas_profesional
- `TurnoFiltros` (query): estado?, desde?, hasta?, page, size
- `ChatbotReservarRequest` (interno): cliente_id, profesional_id, servicio_id, fecha, hora_inicio
- `ChatbotReservarResponse`: turno_id, estado, profesional_nombre, servicio_nombre, fecha, hora_inicio, hora_fin

**Rationale**: Request/Response separation, validación temprana, documentación OpenAPI clara.

### 6. Validación de Unicidad de Slot (Concurrencia)
**Decisión**: Usar `SELECT FOR UPDATE` en transacción + constraint unique DB + retry logic.

**Implementación**:
```python
# En TurnoService.crear_reserva_manual
async with session.begin():
    # Lock row-level en turnos del profesional en ese rango
    stmt = select(Turno).where(
        Turno.profesional_id == prof_id,
        Turno.fecha_inicio >= inicio_rango,
        Turno.fecha_inicio < fin_rango,
        Turno.estado.in_([PENDIENTE, CONFIRMADO, EN_CURSO])
    ).with_for_update()
    # Verificar solapamiento en memoria + DB constraint
```

**Rationale**: SQLite no soporta `SELECT FOR UPDATE` nativamente, pero SQLAlchemy emula. Constraint unique en `(profesional_id, fecha_inicio, servicio_id)` previene race conditions a nivel DB.

### 7. Transiciones de Estado (State Machine)
**Decisión**: Validar transiciones en `TurnoService.cambiar_estado()` usando matriz explícita:

```python
TRANSICIONES_VALIDAS = {
    TurnoEstado.PENDIENTE: [TurnoEstado.CONFIRMADO, TurnoEstado.CANCELADO_CLIENTE, TurnoEstado.CANCELADO_PROFESIONAL],
    TurnoEstado.CONFIRMADO: [TurnoEstado.EN_CURSO, TurnoEstado.CANCELADO_CLIENTE, TurnoEstado.CANCELADO_PROFESIONAL],
    TurnoEstado.EN_CURSO: [TurnoEstado.FINALIZADO, TurnoEstado.NO_ASISTIO, TurnoEstado.CANCELADO_PROFESIONAL],
    TurnoEstado.FINALIZADO: [],  # Inmutable
    TurnoEstado.CANCELADO_CLIENTE: [],
    TurnoEstado.CANCELADO_PROFESIONAL: [],
    TurnoEstado.NO_ASISTIO: [],
}
```

**Rationale**: Explícito, testeable, evita estados inválidos. Solo profesional/Admin pueden mover hacia EN_CURSO/FINALIZADO/NO_ASISTIO.

### 8. Migración Alembic
**Decisión**: Una migración que crea tablas `turnos` y `clientes` con FKs a `users`, `profesionales`, `servicios`.

**Rationale**: Tablas nuevas, no hay datos existentes que migrar. Índices según `__table_args__` del modelo.

### 9. Tests
**Decisión**: 
- Unit: `TurnoService` (mock repo), `TurnoRepo` (DB real con fixture), `SlotService` (ya existe, extender)
- Integración: Endpoints cliente/profesional con `AsyncClient` + auth headers
- Fixtures: `profesional_con_servicios_y_disponibilidad`, `cliente_autenticado`, `turno_confirmado`

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Race condition en reserva concurrente | DB unique constraint + SELECT FOR UPDATE en transacción + test de concurrencia |
| SQLite no soporta FOR UPDATE nativo | SQLAlchemy emula; constraint unique es última barrera |
| Timezone handling (UTC vs local) | Guardar todo en UTC (DateTime timezone=True), convertir en frontend |
| Turnos pasados inmutables | Validar en Service: solo permitir cambios si estado en {PENDIENTE, CONFIRMADO, EN_CURSO} |
| Aislamiento datos profesional/cliente | Query filters obligatorios en Repo (`cliente_id = current_user.cliente_id`, `profesional_id = current_user.profesional_id`) |
| Slot generation performance (60 días) | Límite 60 días ya en SlotService; índices en turnos(profesional_id, fecha_inicio) |
| Chatbot endpoint security | API key header separada, no JWT; rate limit estricto |

## Migration Plan

1. Crear `schemas/turno.py`
2. Completar `models/turno.py` y `models/cliente.py`
3. Crear `repositories/turno_repo.py`
4. Crear `services/turno_service.py`
5. Crear `api/v1/turnos.py` (cliente)
6. Extender `api/v1/profesionales_me.py` con endpoints de turnos
7. Crear `api/v1/chat.py` (endpoint interno)
8. Registrar routers en `main.py`
9. Generar migración Alembic: `alembic revision --autogenerate -m "add turnos and clientes tables"`
10. Ejecutar migración: `alembic upgrade head`
11. Tests unitarios + integración
12. Lint + typecheck + pytest pass

## Open Questions

1. **¿Configurar plazo de cancelación cliente (2h) via env var o DB setting?**
   - Por ahora: constante en Service (`CANCELACION_CLIENTE_HORAS_ANTES = 2`), configurable después.

2. **¿Campo `notas` único o separado `notas_cliente`/`notas_profesional`?**
   - Spec dice ambos. Modelo actual tiene solo `notas`. Decisión: agregar `notas_cliente` y `notas_profesional` en migración.

3. **¿Endpoint `/turnos/disponibilidad` agrupa por profesional o lista plana?**
   - Spec: "Lista de profesionales con sus slots libres agrupados por fecha". Implementar agrupado en Service/Response.

4. **¿Incluir `servicio_id` en consulta de disponibilidad?**
   - Spec: filtro opcional. Slot duration depende del servicio. SlotService usa `profesional.slot_duracion_min` (base). Para filtrar por servicio, necesitaríamos generar slots por servicio. Decisión: v1 usa slot base del profesional; filtro por servicio solo valida que el servicio pertenezca al profesional al reservar.