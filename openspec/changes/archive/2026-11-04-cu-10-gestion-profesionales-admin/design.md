# Design: CU-10 Gestión de profesionales por el administrador

## Context

El motivo está en proposal.md y el comportamiento en `specs/`. Estado actual:

- `ProfesionalService.desactivar_profesional` cuenta turnos con `get_with_turnos_count` y lanza `ValueError` (el endpoint lo traduce a 409). `actualizar_profesional` aplica cualquier `ProfesionalUpdate`, incluido `activo`.
- `get_with_turnos_count` filtra `Turno.fecha_inicio >= func.date(func.now())`: fecha UTC real de SQLite, no la hora del negocio.
- `GET /admin/profesionales` devuelve `ProfesionalResponse` (con `email`, `telefono`, `activo`) y acepta `q` y `activo`. `GET /admin/turnos` acepta `estado` (un valor), `desde`, `hasta`, `profesional_id` y `cliente_id`, y devuelve `TurnoResponse` con los nombres legibles.
- `api.ts` ya tiene `getProfesionalesAdmin`, `crearProfesionalAdmin`, `actualizarProfesionalAdmin`, `desactivarProfesionalAdmin` y `getAllTurnosAdmin`.

## Goals / Non-Goals

**Goals:**
- Una sola regla de baja para `PUT` y `DELETE`.

**Non-Goals:**
- Endpoints nuevos: el dashboard usa los listados existentes (`total` con `activo=true` y `activo=false`).

## Decisions

### 1. Regla de baja compartida
`ProfesionalService._validar_baja(profesional_id)` lanza `ValueError` con la cantidad de turnos. La usan `desactivar_profesional` y `actualizar_profesional` cuando `data.activo is False` y el profesional está activo. El endpoint `PUT` traduce `ValueError` a 409 (hoy no captura nada).

`get_with_turnos_count` cuenta turnos PENDIENTE, CONFIRMADO o EN_CURSO con `Turno.fecha_fin > ahora_negocio()`.
- *Alternativa*: quitar `activo` de `ProfesionalUpdate` y forzar `DELETE`. Se descarta porque `PUT activo: true` es la forma de reactivar.

### 2. Páginas del admin
- **ProfesionalesPage**: tabla/lista paginada (20), búsqueda con debounce y selector Activos / Inactivos / Todos. "Nuevo profesional" y "Editar" usan el `Dialog` de CU-08 con un formulario; en la edición no se muestran email ni contraseña. "Desactivar" pide confirmación y muestra el `detail` del 409; "Reactivar" envía `activo: true`.
- **TurnosPage (admin)**: lista paginada (20) como la del historial del proveedor, sin panel de acciones. El filtro de profesional se llena con `getProfesionalesAdmin({ size: 100 })`. El estado se filtra por un solo valor (el endpoint admin no se cambia en este CU).
- **DashboardPage (admin)**: dos contadores (activos e inactivos) con `size: 1` para leer `total`, y tarjetas con enlaces.
- Se reutilizan `Paginacion`, `ESTADO_LABEL`/`ESTADO_COLOR` y `Dialog`.

### 3. Tipos
`Profesional` (respuesta admin/perfil) pasa a reflejar `ProfesionalResponse`: `email`, `telefono`, `created_at`, `updated_at`; se quitan `servicios`, `disponibilidad` y `excepciones`, que no vienen en esa respuesta. `ProfesionalCreate` pierde `servicios` y suma `telefono`; `ProfesionalUpdate` suma `telefono`. Se revisan los usos con `npm run build`.

## Risks / Trade-offs

- [Cambiar `Profesional` puede romper usos existentes] → `tsc` los marca; hoy solo lo usan `getMiPerfil` y las llamadas admin.
- [Dashboard con dos llamadas] → Es barato; evita un endpoint nuevo.
- [El proveedor desactivado sigue entrando a su panel] → Fuera de alcance; queda documentado en la propuesta.
