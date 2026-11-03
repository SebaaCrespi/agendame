# Design: CU-04 Reserva manual

## Context

El motivo está en proposal.md y el comportamiento esperado en `specs/turnos` y `specs/profesionales`. Las restricciones actuales que condicionan el enfoque son tres:

- Los turnos se guardan con la **hora de reloj del negocio etiquetada como UTC**: `datetime.combine(fecha, hora).replace(tzinfo=UTC)`. Los slots se generan con la misma convención, pero "ahora" se compara contra el UTC real, y ahí aparece el desfase de 3 h.
- La lógica que arma el horario efectivo (grilla semanal + excepciones) y los slots vive en `SlotRepo._generate_slots`. La reserva (`TurnoService.crear_reserva_manual`) no la usa: solo controla que no haya solapamiento.
- `ProfesionalResponse` declara `email`, pero `Profesional` no tiene ese atributo (el email está en `User`). El listado público y el del admin responden 500. No hay tests de los endpoints de profesionales.

## Goals / Non-Goals

**Goals:**
- Que lo que la disponibilidad muestra como libre sea exactamente lo que se puede reservar, generado por una sola implementación.
- Corregir el cálculo de "ahora" sin migrar datos.

**Non-Goals:**
- Guardar UTC real y convertir en los bordes del sistema (ver Decisión 1).
- Tests automatizados de frontend: no hay framework de tests en `frontend/`. El frontend se verifica a mano en el navegador.

## Decisions

### 1. Mantener "hora del negocio con etiqueta UTC" y agregar `ahora_negocio()`
Nuevo módulo `app/core/timeutils.py` con `ahora_negocio()`. Devuelve la hora de reloj actual en `settings.BUSINESS_TIMEZONE`, etiquetada como UTC, para compararla de igual a igual con lo guardado. Reemplaza `datetime.now(UTC)` en las reglas de negocio: pasado, cancelación con 2 h de antelación y generación de slots.
- *Alternativa*: guardar UTC real y convertir en la API. Es más correcta, pero exige migrar datos, tocar la generación de slots y cambiar lo que recibe el frontend. Queda fuera de este CU.
- Los timestamps de auditoría (`confirmado_en`, `cancelado_en`, `created_at`) siguen en UTC real.
- `tzdata` pasa a ser dependencia, porque `zoneinfo` no trae la base de zonas horarias en Windows.

### 2. La reserva valida contra los mismos slots que muestra la disponibilidad
`TurnoService.crear_reserva_manual` llama a `SlotService.generar_slots_disponibles(prof_id, fecha, fecha, duracion_min=servicio.duracion_min)` y busca el slot que empieza en `hora_inicio`:
1. Si el inicio ya pasó según `ahora_negocio()` → 422.
2. Si no hay slot con ese inicio (fuera de horario, día cerrado, no entra antes del cierre, desalineado) → 422.
3. Si el slot existe pero no está disponible (solapamiento) → 409.

Todo esto corre dentro del lock por profesional que ya existe, con commit antes de liberarlo. Así se conserva la garantía de concurrencia. `_validate_slot_libre` deja de usarse en la reserva; la reasignación lo sigue usando.
- *Alternativa*: una función aparte `validar_horario()` en TurnoService. Se descarta porque duplicaría la lógica de grilla y excepciones, y las dos copias podrían divergir de lo que ve el cliente.

### 3. Generación de slots con duración del servicio
`SlotRepo.get_slots_disponibles` y `_generate_slots` reciben un `duracion_min` opcional (por defecto, la duración de slot del profesional):
- El paso entre inicios sigue siendo `slot_duracion_min`, que es la granularidad.
- Cada slot cubre `[inicio, inicio + duracion_min)`. Solo se genera si termina dentro del horario efectivo, y solo está disponible si no se solapa con turnos activos.
- Un slot cuyo inicio es `<= ahora_negocio()` se genera con `disponible = False`. Sigue apareciendo para que la grilla se vea completa.
- `hora_fin` del slot pasa a ser `inicio + duracion_min`.

`TurnoService.consultar_disponibilidad` pasa la duración del servicio cuando recibe `servicio_id`.

### 4. Esquemas de profesional
- Se agrega la propiedad `Profesional.email`, que devuelve `self.user.email` (`user` ya se carga con `selectin`). Con eso vuelven a funcionar `ProfesionalResponse` y los endpoints del admin y de `/me`, sin tocar sus contratos.
- Nuevo `ProfesionalPublicResponse` (sin `email` ni `user_id`, con `servicios: list[ServicioPublicResponse]`) para el listado y el detalle públicos. Los servicios se filtran a los activos y se ordenan por `orden`, al mapear la respuesta en el controller.
- *Alternativa*: reutilizar `ProfesionalResponse` en lo público. Se descarta porque expondría datos de contacto privados.

### 5. Frontend
- `loadDisponibilidad(prof, servicio, fecha)` recibe los valores como parámetros en lugar de leerlos del estado. Esto corrige el bug de estado desactualizado al elegir servicio y al cambiar de semana.
- `api.getProfesionalesPublic` devuelve `data.items`, y el tipo `ProfesionalPublic` se ajusta al nuevo esquema.
- Precio: `formatPrecio(centavos)` con `Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' })`.
- Los slots no disponibles se muestran deshabilitados.

### 6. Datos de prueba
Nuevo script `backend/scripts/seed_dev.py`, idempotente. Crea en la DB de desarrollo un admin, dos profesionales con grilla, servicios de 30 y 60 min y un cliente. Las credenciales de prueba quedan documentadas en el mismo script. Se usa para verificar el flujo en el navegador.

## Risks / Trade-offs

- [Una zona horaria para todo el negocio] → Alcanza para el TP (una peluquería en Argentina). Si hace falta, más adelante se puede pasar a una zona por profesional.
- [Lock en memoria] → Solo protege con un proceso de uvicorn. Ya está documentado en el código; para varios workers haría falta una restricción en la DB o Postgres.
- [Tests dependientes de la hora actual] → Los tests de "pasado" usan fechas relativas (`proximo_dia_habil`) o parchean `ahora_negocio()`, para no depender de la hora a la que se corren.
- [Cambio de `hora_fin` en los slots] → El frontend la muestra como fin del turno, que es lo correcto. Ningún otro consumidor depende del valor anterior.

## Migration Plan

No hay cambios de esquema de DB ni migraciones Alembic. Los turnos existentes siguen siendo válidos. Para desplegar: `pip install -r requirements.txt` (agrega `tzdata`) y reiniciar el backend. Rollback: revertir el commit.
