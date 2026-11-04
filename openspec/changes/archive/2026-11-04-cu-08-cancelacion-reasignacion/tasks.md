# Tasks: CU-08 Cancelación o reasignación de turnos

## 1. Auditoría de reasignación (modelo y migración)

- [x] 1.1 Agregar `reasignado_desde`, `motivo_reasignacion` y `reasignado_en` a `Turno` y a `TurnoResponse`, y crear la migración Alembic (upgrade con `add_column`, downgrade con `batch_alter_table`). Verificar: `alembic upgrade head`, luego `alembic downgrade -1` y de nuevo `alembic upgrade head` sobre una copia de la DB de desarrollo

## 2. Slots y validación compartida

- [x] 2.1 Agregar `excluir_turno_id` a `SlotRepo.get_slots_disponibles` / `_get_turnos_ocupados` y a `SlotService.generar_slots_disponibles`. Verificar: test de servicio de que, excluyendo un turno, su slot figura disponible
- [x] 2.2 Extraer `TurnoService._validar_slot` (pasado → 422, sin slot → 422, ocupado → 409) y usarlo en `crear_reserva_manual`; eliminar `_validate_slot_libre`. Verificar: los tests de CU-04 y de concurrencia siguen en verde

## 3. Reasignación y cancelación del proveedor

- [x] 3.1 `reasignar_turno` usa `_validar_slot` con `excluir_turno_id` y `TurnoRepo.reasignar` guarda la auditoría. Verificar: tests de servicio para slot libre (el horario anterior queda libre), 03:00 → 422, día cerrado → 422, ocupado → 409, corrimiento de 60 min sobre sí mismo y auditoría en la respuesta
- [x] 3.2 `cancelar_turno_profesional` rechaza PENDIENTE o CONFIRMADO ya empezados (422) y permite EN_CURSO. Verificar: tests de servicio con el reloj parcheado y test de API `PUT /cancelar` → 422 para un turno pasado

## 4. Endpoint de slots del proveedor

- [x] 4.1 Crear `GET /profesionales/me/slots` (`desde`, `hasta`, `servicio_id`, `excluir_turno_id`) que responda 404 si el servicio es ajeno. Verificar: tests de API para excluir turno, duración del servicio, servicio ajeno → 404 y rango mayor a 60 días → 400

## 5. Frontend

- [x] 5.1 Crear `components/ui/Dialog.tsx` y `components/turnos/CancelarDialog.tsx`, y reemplazar el `prompt()`/`alert()` del cliente en `ClienteDashboard`. Verificar: `npm run build`
- [x] 5.2 Crear `components/turnos/ReasignarDialog.tsx`, sumar `getMisSlots` y los tipos en `api.ts`/`types/index.ts`, y agregar las acciones "Cancelar" y "Reasignar" en `TurnoDetallePanel` según el estado y la hora. Verificar: `npm run build` y `npm run lint` sin errores

## 6. Verificación end-to-end

- [x] 6.1 En el navegador:
  - Como cliente: cancelar un turno desde "Mis turnos" con un motivo.
  - Como Juan: reasignar un turno a otro día y horario (verificar que aparece en la grilla y que el horario anterior queda libre en la reserva del cliente), cancelar otro turno con motivo, y comprobar que los turnos pasados no ofrecen "Cancelar".
  - Revisar los diálogos a 375 px.

  Verificar: capturas
- [x] 6.2 Suite completa en verde y `ruff check app/` limpio. Verificar: `pytest` y `ruff check app/`

## Workflow follow-up

- `/opsx-archive` del change una vez implementado y revisado
- `mem_save` en Engram con las decisiones (`_validar_slot` compartido, auditoría en columnas)
