# Proposal: CU-04 Reserva manual de turno desde el Frontend

## Why

CU-04 pide que el cliente elija visualmente profesional, servicio, fecha y horario disponible y confirme el turno. El backend de reservas existe (archivado en `cu-03-turnos`), pero el flujo completo no funciona hoy:

- El listado de profesionales (`GET /profesionales`), primer paso del flujo, responde 500: `ProfesionalResponse` exige `email` y el modelo `Profesional` no lo tiene.
- La pantalla de reserva nunca carga los horarios: `loadDisponibilidad` lee estado de React viejo y sale sin consultar.
- La disponibilidad ofrece horarios en los que el servicio no entra (ignora su duración) y horarios de hoy que ya pasaron.
- La reserva acepta horarios fuera de la grilla del profesional (ej. 03:00) o en días cerrados por excepción.
- "Ahora" se calcula en UTC mientras los horarios se guardan como hora local del negocio, así que la validación de "turno en el pasado" se corre 3 horas.

## What Changes

- **Validación de horario en la reserva**: el turno completo (inicio + duración del servicio) debe caer dentro del horario efectivo del día (grilla semanal + excepciones) y empezar en un múltiplo de la granularidad del profesional. Si no, 422.
- **Disponibilidad según el servicio**: con `servicio_id`, un horario figura disponible solo si el servicio completo entra libre antes del cierre. Los horarios ya pasados figuran como no disponibles.
- **Zona horaria del negocio**: nueva configuración `BUSINESS_TIMEZONE` (por defecto `America/Argentina/Buenos_Aires`) para calcular "ahora". También aplica a la regla de cancelación con más de 2 horas de antelación.
- **Listado público de profesionales**: deja de fallar, no expone el email del profesional e incluye sus servicios activos, que el frontend necesita.
- **Frontend `ClienteDashboard`**: se corrige la carga de disponibilidad al elegir servicio y al cambiar de semana, el consumo del listado paginado y el precio (está guardado en centavos).
- **Verificación end-to-end** del flujo en el navegador con datos de prueba (seed).

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `turnos`: la reserva manual valida que el turno caiga dentro del horario de atención; la consulta de disponibilidad tiene en cuenta la duración del servicio y los horarios pasados; "ahora" se calcula en la zona horaria del negocio.
- `profesionales`: el listado público devuelve profesionales activos con sus servicios activos y sin datos de contacto privados.

## Impact

- **Backend**: `services/turno_service.py`, `repositories/slot_repo.py`, `schemas/profesional.py`, `api/v1/profesionales_public.py`, `core/config.py`, y `requirements.txt` (agrega `tzdata`, que `zoneinfo` necesita en Windows).
- **Frontend**: `pages/cliente/DashboardPage.tsx`, `services/api.ts`, `types/index.ts`.
- **Tests**: nuevos casos en `tests/services/test_turno_service.py`, `tests/api/v1/test_turnos.py` y tests del listado público.
- **API**: el listado público deja de devolver `email` y `user_id` y suma `servicios`. No es un breaking change real, porque el endpoint hoy responde 500.

## Fuera de alcance

- Acceso de visitantes sin login a profesionales y grillas (CU-03).
- Vistas del proveedor y del admin (CU-07, CU-10) y reasignación desde el frontend (CU-08).
- Chatbot (CU-05, CU-06) y notificaciones.
- Soporte multi-zona horaria por profesional.
