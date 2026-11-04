# Design: CU-08 Cancelación o reasignación de turnos

## Context

El motivo está en proposal.md y el comportamiento en `specs/turnos`. Restricciones del código actual:

- `crear_reserva_manual` (CU-04) valida contra `SlotService.generar_slots_disponibles(..., duracion_min)` bajo un lock por profesional y commitea dentro del lock.
- `reasignar_turno` solo comprueba que no haya solapamiento (excluyendo el propio turno), y `TurnoRepo.reasignar` descarta el motivo.
- `SlotRepo._get_turnos_ocupados` no permite excluir un turno.
- No hay en el frontend ningún componente de diálogo ni librería de UI que lo provea.

## Goals / Non-Goals

**Goals:**
- Una sola regla de "slot válido" para reservar y para reasignar.
- Que el proveedor elija el nuevo horario entre opciones válidas, en lugar de escribir uno a mano.

**Non-Goals:**
- Una tabla de historial con varios eventos por turno.
- Una librería de componentes UI.

## Decisions

### 1. Helper de validación de slot compartido
`TurnoService._validar_slot(profesional_id, fecha, hora_inicio, duracion_min, excluir_turno_id=None)` encapsula la validación de CU-04:
1. Si el horario es pasado según `ahora_negocio()` → 422.
2. Si no existe un slot que empiece a esa hora → 422.
3. Si el slot existe pero no está disponible → 409.

La usan `crear_reserva_manual` y `reasignar_turno`, siempre dentro de `_reserva_locks[profesional_id]` y con commit antes de soltar el lock. `_validate_slot_libre` deja de usarse y se elimina.

### 2. Excluir un turno de los ocupados
`SlotRepo.get_slots_disponibles` y `SlotService.generar_slots_disponibles` aceptan `excluir_turno_id`. `_get_turnos_ocupados` lo filtra con `Turno.id != excluir_turno_id`. La reasignación lo usa para que el turno no se bloquee a sí mismo; el endpoint del proveedor lo expone para que el diálogo muestre como libre el horario actual.

### 3. Auditoría en columnas del turno
Columnas nuevas en `turnos`, todas nullable: `reasignado_desde` (DateTime tz, el inicio anterior), `motivo_reasignacion` (Text) y `reasignado_en` (DateTime tz, en UTC real, como los demás timestamps de auditoría). Se agrega una migración Alembic que solo hace `add_column`, por lo que en SQLite no requiere batch.
- *Alternativa*: una tabla `turno_eventos`. Se descarta porque el spec solo pide registrar la última reasignación; si más adelante hace falta un historial completo, se puede migrar.

### 4. Cancelación del proveedor
En `cancelar_turno_profesional`, después de validar el estado: si el turno está PENDIENTE o CONFIRMADO y `_aware(fecha_inicio) <= ahora_negocio()` → 422 con el mensaje "El turno ya empezó: marcalo como ausente o finalizado". EN_CURSO se puede cancelar.

### 5. Endpoint `GET /profesionales/me/slots`
Parámetros: `desde`, `hasta` (máximo 60 días), `servicio_id` opcional y `excluir_turno_id` opcional. Usa `get_mi_profesional` (CU-07). Si se pasa `servicio_id`, este tiene que ser del profesional (si no, 404) y su duración define la de los slots. Devuelve `SlotsListResponse`, el mismo esquema que los slots públicos.

### 6. Diálogos en el frontend
- **`components/ui/Dialog.tsx`**: overlay `fixed` con un panel centrado, que se cierra con Escape o con el botón de cerrar. Pone el foco en el primer campo y tiene `role="dialog"` y `aria-modal`. En mobile ocupa el ancho con 16 px de margen.
- **`CancelarDialog`**: motivo obligatorio (1–500 caracteres) y confirmación. Lo usan el cliente (`cancelarTurnoCliente`) y el proveedor (`cancelarTurnoProfesional`); el componente recibe por props qué función llamar.
- **`ReasignarDialog`** (solo para el proveedor): fecha (desde hoy), slots del día pedidos con `servicio_id` y `excluir_turno_id`, botones solo para los disponibles, y motivo.
- El diálogo muestra el `detail` del backend si falla. Si la respuesta es 409, vuelve a cargar los slots.
- En `TurnoDetallePanel`, "Cancelar" y "Reasignar" se muestran según el estado (reasignar: PENDIENTE o CONFIRMADO; cancelar: también EN_CURSO), y para PENDIENTE o CONFIRMADO solo si el turno es futuro.

## Risks / Trade-offs

- [Se guarda solo la última reasignación] → Es aceptable para el TP y queda documentado en el spec.
- [Diálogo hecho a mano] → No atrapa el foco del todo, más allá del foco inicial y el cierre con Escape. Es suficiente para el alcance del TP.
- [Cambio de comportamiento: el proveedor ya no puede cancelar turnos pasados] → Es lo que pide el spec; para esos casos se usa NO_ASISTIO.

## Migration Plan

1. `alembic upgrade head` agrega las 3 columnas nullable; los turnos existentes quedan con NULL.
2. Rollback: `alembic downgrade -1` elimina las columnas. En SQLite necesita SQLite 3.35 o superior, o `batch_alter_table`; la migración usa `batch_alter_table` en el downgrade.
