# Proposal: CU-08 Cancelación o reasignación de turnos

## Why

CU-08 pide que el cliente pueda cancelar su turno y que el proveedor lo modifique por fuerza mayor, liberando el espacio en la grilla. El backend ya tiene los endpoints (archivados en `cu-03-turnos`), pero:

- **La reasignación no valida el horario.** Un turno se puede mover a las 03:00 o a un día cerrado: no aplica las reglas de grilla que CU-04 agregó a la reserva.
- **La reasignación no deja registro.** El motivo se recibe y se descarta, y no queda guardado cuál era el horario anterior. El spec de turnos (RF-TURNO-05) pide auditoría.
- **El proveedor puede cancelar turnos que ya pasaron.** El spec dice "cualquier turno futuro"; un turno pasado que no se atendió es un NO_ASISTIO (CU-07).
- **El proveedor no tiene cómo ver horarios libres para reasignar.** Las consultas de disponibilidad solo admiten el rol CLIENTE.
- **Frontend:** el cliente cancela con un `prompt()` del navegador y ve un `alert()` genérico si falla. El proveedor no tiene ninguna interfaz para cancelar ni reasignar.

## What Changes

- **Reasignación validada contra los slots**: el nuevo horario debe ser un slot disponible del profesional para la duración del servicio, con la misma regla que la reserva de CU-04. El propio turno no cuenta como ocupado. Si el horario está fuera de la grilla, desalineado o es pasado → 422; si está ocupado → 409.
- **Auditoría de reasignación**: el turno guarda el horario anterior, el motivo y cuándo se reasignó, y los devuelve en la respuesta.
- **Cancelación del proveedor solo para turnos futuros**: los que ya empezaron responden 422, salvo los que están EN_CURSO, que se pueden cancelar por fuerza mayor.
- **Disponibilidad para el proveedor**: nuevo `GET /profesionales/me/slots` con rango de fechas, servicio y un turno a excluir.
- **Frontend cliente**: un diálogo de cancelación con motivo obligatorio y el error del backend visible.
- **Frontend proveedor**: en el detalle del turno, acciones "Cancelar" (con motivo) y "Reasignar" (elegir fecha y slot libre, con motivo).

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `turnos`: la reasignación se valida contra los slots y se audita; la cancelación del proveedor se limita a turnos futuros o en curso; nueva consulta de disponibilidad para el proveedor.

## Impact

- **Backend**: `models/turno.py` (3 columnas nuevas), una migración Alembic, `services/turno_service.py`, `repositories/turno_repo.py`, `schemas/turno.py` y `api/v1/profesionales_me.py`.
- **Frontend**: `components/turnos/TurnoDetallePanel.tsx`, nuevos `components/turnos/CancelarDialog.tsx` y `components/turnos/ReasignarDialog.tsx`, `pages/cliente/DashboardPage.tsx`, `services/api.ts` y `types/index.ts`.
- **DB**: la migración agrega columnas que aceptan nulos, así que no rompe los turnos existentes.

## Fuera de alcance

- Reasignar a otro profesional o cambiar el servicio.
- Que el cliente reprograme su propio turno (solo puede cancelar y volver a reservar).
- Notificaciones al cliente cuando el proveedor cancela o reasigna.
- Historial de varias reasignaciones: se guarda solo la última.
