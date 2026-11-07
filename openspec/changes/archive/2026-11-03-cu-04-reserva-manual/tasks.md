# Tasks: CU-04 Reserva manual

## 1. Hora del negocio

- [x] 1.1 Agregar `tzdata` a `backend/requirements.txt` e instalarlo. Agregar `BUSINESS_TIMEZONE` (default `America/Argentina/Buenos_Aires`) a `core/config.py` y a `.env.example`. Verificar: `python -c "from zoneinfo import ZoneInfo; ZoneInfo('America/Argentina/Buenos_Aires')"` no falla
- [x] 1.2 Crear `app/core/timeutils.py` con `ahora_negocio()`, que devuelve la hora de reloj del negocio etiquetada como UTC. Verificar: test en `tests/test_timeutils.py` que parchea el reloj (00:30 UTC → 21:30 del día anterior)
- [x] 1.3 Reemplazar `datetime.now(UTC)` por `ahora_negocio()` en las reglas de pasado y de cancelación con 2 h de antelación de `TurnoService`. Verificar: test de servicio "cancelación con hora local" del spec y suite de turnos en verde

## 2. Slots según la duración del servicio

- [x] 2.1 `SlotRepo.get_slots_disponibles` / `_generate_slots`: agregar el parámetro `duracion_min` (por defecto, la duración de slot del profesional). El slot debe entrar entero antes del cierre, el solapamiento se evalúa sobre la duración completa, los inicios ya pasados quedan `disponible=False` y `hora_fin = inicio + duracion`. Verificar: tests de "servicio largo antes de turno ocupado", "servicio largo al cierre" y "slots de hoy que ya pasaron"
- [x] 2.2 Pasar `duracion_min` desde `SlotService.generar_slots_disponibles` y desde `TurnoService.consultar_disponibilidad` cuando hay `servicio_id`. Verificar: test de API `GET /turnos/disponibilidad` con un servicio de 60 min que no ofrece las 17:30

## 3. Validación de la reserva contra los slots

- [x] 3.1 En `crear_reserva_manual`, bajo el lock: rechazar con 422 si es pasado, con 422 si no existe un slot con ese inicio, y con 409 si el slot no está disponible (ver design, Decisión 2). Verificar: tests de servicio para fuera de horario, no entra antes del cierre, día sin grilla, excepción CERRADO, HORARIO_ESPECIAL e inicio desalineado
- [x] 3.2 Tests de API de `POST /turnos` para 07:00 → 422 y 09:10 → 422, más los tests de concurrencia y del endpoint interno del chatbot siguiendo en verde. Verificar: `pytest tests/api/v1/test_turnos.py tests/test_concurrency.py tests/api/v1/test_chat.py`

## 4. Listado público de profesionales

- [x] 4.1 Agregar la propiedad `Profesional.email` (desde `user`). Verificar: test de API `GET /admin/profesionales` responde 200 con el email
- [x] 4.2 Crear `ProfesionalPublicResponse` y `ServicioPublicResponse`, y usarlos en `GET /profesionales` y `GET /profesionales/{id}`: solo servicios activos ordenados por `orden`, sin `email` ni `user_id`. Verificar: nuevo `tests/api/v1/test_profesionales_public.py` con los escenarios del spec de profesionales

## 5. Frontend de reserva

- [x] 5.1 `services/api.ts` y `types/index.ts`: `getProfesionalesPublic` devuelve `items` y el tipo `ProfesionalPublic` refleja el nuevo esquema. Verificar: `npm run build` sin errores de tipos
- [x] 5.2 `ClienteDashboard`: `loadDisponibilidad(prof, servicio, fecha)` con parámetros explícitos al elegir servicio y al navegar semanas, slots no disponibles deshabilitados y precio con `formatPrecio`. Verificar: `npm run build` y `npm run lint` sin errores

## 6. Datos de prueba y verificación end-to-end

- [x] 6.1 Crear `backend/scripts/seed_dev.py`, idempotente, con admin, dos profesionales con grilla, servicios de 30 y 60 min y un cliente, y las credenciales de prueba documentadas en el script. Verificar: correrlo dos veces no duplica datos
- [x] 6.2 Verificación en el navegador con backend y frontend levantados: login como cliente → elegir profesional → servicio → semana → horario → confirmar. El turno aparece en "Mis turnos" y el horario queda ocupado; reservar el mismo horario muestra el error del backend. Verificar: capturas del flujo
- [x] 6.3 Suite completa en verde y `ruff check app/` limpio. Verificar: `pytest` y `ruff check app/`

## Workflow follow-up

- `/opsx-archive` del change una vez implementado y revisado
- `mem_save` en Engram con las decisiones clave (hora del negocio, una sola validación vía slots)
