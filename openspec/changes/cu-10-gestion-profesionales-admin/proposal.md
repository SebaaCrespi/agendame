# Proposal: CU-10 Gestión de profesionales por el administrador

## Why

CU-10 pide que el administrador dé de alta, modifique y dé de baja peluqueros, cada uno con su grilla independiente. El backend (`/admin/profesionales`, `/admin/turnos`) existe, pero las tres pantallas del admin ("Dashboard", "Todos los Turnos" y "Profesionales") dicen "Próximamente". Además:

- **La baja se puede saltear**: `PUT /admin/profesionales/{id}` con `activo: false` desactiva sin el control de turnos futuros que sí hace `DELETE`.
- **El control de turnos futuros usa la fecha UTC real** (`func.date(func.now())`) en vez de la hora del negocio, y cuenta turnos de hoy que ya terminaron.
- **Los tipos del frontend no coinciden con la API**: `Profesional` no tiene `email` ni `telefono`, y `ProfesionalCreate` declara `servicios`, que el backend no recibe.

## What Changes

- **Baja consistente**: desactivar por `PUT` (`activo: false`) aplica la misma regla que `DELETE`: 409 si el profesional tiene turnos PENDIENTE, CONFIRMADO o EN_CURSO que todavía no terminaron (según la hora del negocio). Reactivar (`activo: true`) no tiene restricciones.
- **Página "Profesionales"** (`/admin/profesionales`): lista paginada con búsqueda por nombre y filtro activos/inactivos; alta (nombre, apellido, email, contraseña temporal, teléfono, duración base del slot) y edición en un diálogo; desactivar con confirmación (mostrando el error si tiene turnos) y reactivar.
- **Página "Todos los turnos"** (`/admin/turnos`): listado paginado de solo lectura con filtros por profesional, estado y rango de fechas.
- **Dashboard del admin**: cantidad de profesionales activos e inactivos, y accesos a las dos páginas.
- Tipos `Profesional`, `ProfesionalCreate` y `ProfesionalUpdate` alineados con la API.

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `profesionales`: la baja de un profesional se controla igual por cualquier vía y según la hora del negocio; se define la gestión del admin desde la interfaz.
- `turnos`: el administrador consulta todos los turnos desde la interfaz.

## Impact

- **Backend**: `services/profesional_service.py` (`actualizar_profesional` valida la baja), `repositories/profesional_repo.py` (`get_with_turnos_count` con `ahora_negocio()`) y tests. Sin cambios de modelo ni de endpoints.
- **Frontend**: nuevas `pages/admin/ProfesionalesPage.tsx`, `TurnosPage.tsx` y `DashboardPage.tsx`; `App.tsx`; `types/index.ts`.

## Fuera de alcance

- Que el admin edite la grilla, servicios o excepciones de un profesional: cada proveedor configura la suya (CU-02).
- Bloquear el acceso del proveedor desactivado a su panel.
- Cambiar el email del usuario del profesional o resetear su contraseña.
- Acciones del admin sobre turnos (cancelar, reasignar): el listado es de solo lectura.
