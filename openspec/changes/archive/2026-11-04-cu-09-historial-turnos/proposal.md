# Proposal: CU-09 Consulta de historial de turnos

## Why

CU-09 pide que cada rol consulte su historial de turnos (pasados, activos y cancelados) con filtros. El backend ya lista turnos paginados por rol, pero el historial no se puede usar:

- **Cliente**: "Mis turnos" es una lista sin filtros que mezcla próximos y pasados. El nombre del profesional y del servicio salen vacíos (el frontend lee `turno.profesional?.nombre`, que la API no devuelve) y la paginación carga la página anterior (llama a `loadMisTurnos` antes de que se aplique el nuevo `page`).
- **Proveedor**: solo tiene la grilla de una semana, limitada a 100 turnos. No puede revisar turnos pasados de varias semanas ni encontrar los que quedaron sin cerrar.
- **API**: el filtro `estado` admite un solo valor, así que "cancelados" (CANCELADO_CLIENTE + CANCELADO_PROFESIONAL) necesita dos consultas. No hay forma de pedir solo próximos o solo pasados con el orden adecuado.

## What Changes

- **Filtro `momento`** (`proximos` | `pasados`) en `GET /turnos/mis-turnos` y `GET /profesionales/me/turnos`. Próximos: turnos que todavía no terminaron, del más cercano al más lejano. Pasados: turnos ya terminados, del más reciente al más viejo. Sin `momento` el orden queda como hoy.
- **Filtro `estado` con varios valores**: se puede repetir (`?estado=CANCELADO_CLIENTE&estado=CANCELADO_PROFESIONAL`). Un solo valor sigue funcionando igual.
- **Frontend cliente**: "Mis turnos" con pestañas Próximos / Pasados, un filtro por grupo de estado (Todos, Activos, Finalizados, Cancelados, No asistió) y rango de fechas. Muestra nombre del profesional y del servicio, el estado legible, el motivo de cancelación y la reasignación. Se corrige la paginación.
- **Frontend proveedor**: nueva página "Historial" (`/profesional/historial`, en el menú) con lista paginada, los mismos filtros más servicio y cliente, y el detalle del turno al hacer clic (reutiliza `TurnoDetallePanel`). Los turnos pasados PENDIENTE o CONFIRMADO se marcan "Sin cerrar".

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `turnos`: el historial por rol se consulta por momento (próximos o pasados) y por varios estados a la vez; se define qué muestra el historial de cada rol.

## Impact

- **Backend**: `schemas/turno.py` (`TurnoFiltros`), `repositories/turno_repo.py` (`get_by_cliente`, `get_by_profesional`), `api/v1/turnos.py` y `api/v1/profesionales_me.py`. Sin cambios en el modelo ni migraciones.
- **Frontend**: `pages/cliente/DashboardPage.tsx`, nueva `pages/profesional/HistorialPage.tsx`, `App.tsx`, `components/layout/Header.tsx`, `types/index.ts` y `services/api.ts`.
- **Compatibilidad**: los parámetros nuevos son opcionales; las llamadas actuales (grilla semanal, admin) no cambian.

## Fuera de alcance

- Cerrar automáticamente los turnos pasados (pasarlos a FINALIZADO o NO_ASISTIO). Solo se señalan como "Sin cerrar".
- Historial global del administrador (`/admin/turnos`), que va con CU-10.
- Exportar el historial (CSV/PDF) y estadísticas.
- Búsqueda del cliente por profesional o servicio.
