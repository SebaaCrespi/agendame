# Design: CU-07 Gestión de grilla y turnos asignados

## Context

Motivo en proposal.md; comportamiento en `specs/turnos`. Restricciones relevantes del código actual:

- `Turno.cliente`, `Turno.servicio`, `Turno.profesional` y `Cliente.user` usan `lazy="selectin"`. Cada vez que se consulta un turno, esas relaciones ya vienen cargadas.
- Los horarios se guardan como hora del negocio con etiqueta UTC (ver el design de CU-04). La API los devuelve unas veces con `+00:00` (objetos recién creados) y otras sin zona (leídos de SQLite).
- El frontend no tiene librería de calendario. Ya usa `date-fns` y Tailwind.

## Goals / Non-Goals

**Goals:**
- Que la grilla muestre los turnos en la hora correcta, sin importar la zona horaria del navegador.
- Que el backend siga siendo la única fuente de verdad sobre qué transiciones de estado son válidas.

**Non-Goals:**
- Arrastrar y soltar turnos en la grilla (sería reasignar, CU-08).
- Agregar una librería de calendario.

## Decisions

### 1. Datos legibles como propiedades del modelo
`Turno` gana las propiedades `cliente_nombre` (`cliente.user.nombre`), `cliente_telefono`, `servicio_nombre` y `profesional_nombre`. `TurnoResponse` las lee con `from_attributes`. Es el mismo patrón que `Profesional.email` en CU-04.
- *Alternativa*: anidar los objetos completos (`cliente: {...}`). Se descarta porque expone más datos de los necesarios (por ejemplo, el email del usuario) y obliga a definir más esquemas.

### 2. Filtros en `TurnoFiltros` y `TurnoRepo.get_by_profesional`
- `TurnoFiltros` suma `servicio_id: int | None` y `cliente: str | None` (de 1 a 100 caracteres).
- El filtro por cliente hace join `Turno → Cliente → User` con `func.lower(User.nombre).contains(texto.lower())`.
- Se aplican sobre la consulta que ya filtra por `profesional_id`, así que un `servicio_id` ajeno devuelve una lista vacía sin necesidad de validarlo aparte.

### 3. Ausencia: transición condicionada por la hora
`TRANSICIONES_VALIDAS[CONFIRMADO]` suma `NO_ASISTIO`. En `cambiar_estado`, si el destino es NO_ASISTIO y el origen CONFIRMADO, se exige `fecha_inicio <= ahora_negocio()`; si no se cumple, `ValidationException` (422). EN_CURSO → NO_ASISTIO se mantiene sin condición.
- *Alternativa*: un endpoint aparte `/no-asistio`. Se descarta porque duplicaría `/estado`.

### 4. Hora de reloj en el frontend
Nuevo helper `utils/horaNegocio.ts`, `parseHoraNegocio(iso)`: descarta el sufijo de zona (`Z` o `±hh:mm`) y parsea el resto como hora local del navegador. Así 10:00 se muestra como 10:00 aunque el navegador esté en otra zona horaria. Lo usan la grilla y, de paso, las tarjetas de "Mis turnos" del cliente.
- *Alternativa*: `new Date(iso)`. Se descarta porque convertiría `10:00+00:00` a 07:00 en Argentina.

### 5. Grilla semanal propia
Componente `components/turnos/WeekGrid.tsx`:
- 7 columnas (lunes a domingo) y un eje de horas.
- El rango de horas sale de la grilla del profesional (`GET /profesionales/me/disponibilidad`): la hora de apertura más temprana y la de cierre más tardía. Si esa consulta falla, usa 08:00–20:00.
- Cada turno es un bloque con posición absoluta (`top` y `height` según los minutos) y color por estado.
- En pantallas angostas el contenedor de la grilla tiene scroll horizontal propio; la página no.

La página `pages/profesional/TurnosPage.tsx` carga la semana con `GET /profesionales/me/turnos?desde&hasta&size=100` más los filtros, y abre un panel de detalle (`TurnoDetallePanel`). Las acciones visibles salen de una tabla `TRANSICIONES` en el frontend que replica la del backend, para no mostrar botones inútiles. Si el backend rechaza el cambio, se muestra su `detail`.

### 6. Redirección por rol
Un componente `RoleRedirect` en `App.tsx` reemplaza las rutas `/` y `*`. Sin usuario, va a `/login`; con usuario, a `/cliente/dashboard`, `/profesional/dashboard` o `/admin/dashboard` según su rol. `ProtectedRoute` ya manda a `/` cuando el rol no coincide; con esto deja de entrar en loop.

### 7. Dashboard del proveedor
`pages/profesional/DashboardPage.tsx`: los turnos de hoy (`desde = hasta = hoy`), un conteo por estado y un enlace a la grilla. No agrega endpoints nuevos.

## Risks / Trade-offs

- [`lower()` de SQLite solo maneja ASCII] → Una búsqueda de "ÁNGEL" no encuentra "ángel". Se acepta para el TP; los nombres se escriben en minúscula o con su capitalización habitual.
- [La tabla `TRANSICIONES` está duplicada en el frontend] → Puede desincronizarse del backend. El backend igual valida y el frontend muestra su error. Se documenta en el archivo que es una copia.
- [Límite de 100 turnos por semana] → Alcanza para un profesional (son 18 slots por día como máximo). Si se llega a 100, la grilla muestra un aviso.

## Migration Plan

Sin cambios de esquema ni migraciones. Los campos nuevos de la respuesta son aditivos.
