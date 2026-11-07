# Proposal: CU-02 Configuración del proveedor (perfil, servicios y disponibilidad)

## Why

CU-02 pide que el proveedor configure su disponibilidad horaria, la duración de sus turnos y sus servicios. El backend (`/profesionales/me/*`) ya lo permite, pero en la aplicación las páginas "Mi Perfil", "Servicios" y "Disponibilidad" dicen "Próximamente": un proveedor nuevo no puede ponerse en marcha sin usar la API a mano.

Además, el backend acepta cambios que dejan turnos activos fuera de horario: si el proveedor acorta su grilla o marca un día como cerrado, los turnos ya reservados quedan huérfanos sin aviso.

## What Changes

- **Página "Mi Perfil"** (`/profesional/perfil`): editar nombre, apellido, teléfono, biografía, URL de foto y duración base del slot.
- **Página "Servicios"** (`/profesional/servicios`): listar los servicios activos, crear, editar (nombre, descripción, duración, precio en pesos, orden) y desactivar con confirmación.
- **Página "Disponibilidad"** (`/profesional/disponibilidad`):
  - Grilla semanal: por cada día, atiende sí/no y horario de inicio y fin; se guarda todo junto.
  - Excepciones: listar las próximas, agregar (día cerrado u horario especial, con motivo) y eliminar.
- **Protección de turnos activos (backend)**: guardar la grilla o agregar una excepción responde 409 si algún turno futuro PENDIENTE, CONFIRMADO o EN_CURSO quedaría fuera del nuevo horario, e informa cuántos y cuáles fechas. El proveedor los reasigna o cancela (CU-08) y vuelve a guardar.
- Errores del backend visibles en cada formulario.

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `profesionales`: los cambios de grilla y las excepciones no pueden dejar turnos activos fuera de horario; se define la configuración del proveedor desde la interfaz.

## Impact

- **Backend**: `services/disponibilidad_service.py` (validación contra turnos activos), `repositories/turno_repo.py` (consulta de turnos activos futuros) y tests. Sin cambios de modelo ni migraciones.
- **Frontend**: nuevas `pages/profesional/PerfilPage.tsx`, `ServiciosPage.tsx` y `DisponibilidadPage.tsx`; `App.tsx` (rutas); `services/api.ts` y `types/index.ts` si faltan tipos.
- **Compatibilidad**: los endpoints no cambian de forma; solo agregan el caso 409.

## Fuera de alcance

- Varios rangos por día (horario cortado, ej. 9–13 y 15–19): el modelo admite un rango por día.
- Reactivar servicios desactivados (el listado del proveedor solo trae activos).
- Subir una foto como archivo: se carga una URL.
- Cambiar email o contraseña del proveedor (ya existe en `/auth/me`).
- Revalidar turnos existentes cuando cambia la duración base del slot o la de un servicio.
