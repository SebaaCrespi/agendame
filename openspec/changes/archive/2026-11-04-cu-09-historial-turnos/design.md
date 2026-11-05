# Design: CU-09 Consulta de historial de turnos

## Context

El motivo está en proposal.md y el comportamiento en `specs/turnos`. Estado actual relevante:

- `TurnoRepo.get_by_cliente` ordena por `fecha_inicio` descendente y `get_by_profesional` ascendente (lo usa la grilla semanal de CU-07). Los dos filtran `estado` con igualdad sobre un solo valor de `TurnoFiltros.estado`.
- Las fechas de turno se guardan como hora del negocio con etiqueta UTC; "ahora" se obtiene con `ahora_negocio()`.
- axios serializa los arrays como `estado[]=A&estado[]=B`, que FastAPI no reconoce como lista.
- `TurnoResponse` ya trae `profesional_nombre`, `servicio_nombre`, `motivo_cancelacion` y la auditoría de reasignación (CU-08).

## Goals / Non-Goals

**Goals:**
- Un solo punto (el repositorio) donde se resuelven `momento`, la lista de estados y el orden, para los dos roles.
- No cambiar el comportamiento de las llamadas existentes sin los parámetros nuevos.

**Non-Goals:**
- Endpoints nuevos: se extienden los listados existentes.
- Cambios en el modelo o migraciones.

## Decisions

### 1. `estado` como lista en `TurnoFiltros`
`TurnoFiltros.estado` pasa a `list[TurnoEstado] | None`. Los endpoints declaran `estado: list[TurnoEstado] | None = Query(None)`, así que un valor inválido da 422 por validación y uno solo llega como lista de un elemento. El repositorio filtra con `Turno.estado.in_(...)`.
- *Alternativa*: valores separados por coma (`estado=A,B`). Se descarta porque requiere parseo propio y la repetición es lo estándar en FastAPI.

### 2. `momento` y orden en el repositorio
Enum `MomentoTurno` (`proximos`, `pasados`) en `schemas/turno.py` y campo `momento` en `TurnoFiltros`. En `get_by_cliente` y `get_by_profesional`, con `ahora = ahora_negocio()`:
- `proximos` → `Turno.fecha_fin > ahora`, orden `fecha_inicio` ascendente.
- `pasados` → `Turno.fecha_fin <= ahora`, orden `fecha_inicio` descendente.
- Sin `momento` → el orden actual de cada método.

Se compara contra `fecha_fin` para que un turno en curso siga en próximos. La lógica común va en un helper privado del repositorio que aplica estado y momento al `select`, para no duplicarla.

### 3. Serialización de arrays en el cliente API
El `ApiClient` configura `paramsSerializer: { indexes: null }` en la instancia de axios, que produce `estado=A&estado=B`. Afecta a todas las llamadas, pero ninguna envía arrays hoy.

### 4. Historial del cliente
En `DashboardPage`, la pestaña "Mis turnos" agrega Próximos / Pasados (`momento`), un selector de grupo de estado y desde/hasta. Los grupos se traducen en el frontend a listas de estados: Activos = PENDIENTE, CONFIRMADO, EN_CURSO; Finalizados = FINALIZADO; Cancelados = CANCELADO_CLIENTE, CANCELADO_PROFESIONAL; No asistió = NO_ASISTIO. La carga se dispara desde un `useEffect` que depende de los filtros (incluido `page`), lo que corrige la paginación. Se usan `profesional_nombre`, `servicio_nombre` y `ESTADO_LABEL`/`ESTADO_COLOR` de `components/turnos/estado.ts`.

### 5. Historial del proveedor
Nueva `pages/profesional/HistorialPage.tsx` en `/profesional/historial` y entrada "Historial" en el menú. Lista paginada (20 por página) con filtros momento (por defecto pasados), estado, desde/hasta, servicio y cliente (con el mismo debounce que `TurnosPage`). Al elegir un turno se abre `TurnoDetallePanel`; `onUpdated` reemplaza el turno en la lista y recarga si cambió de fecha. "Sin cerrar" se calcula en el frontend: estado PENDIENTE o CONFIRMADO y `fecha_fin` ya pasada.

## Risks / Trade-offs

- [`estado` cambia de tipo en `TurnoFiltros`] → Hay que actualizar sus usos (`TurnosPage` envía un solo estado; admin usa su propio parámetro). Los tests existentes de filtros cubren la regresión.
- [`paramsSerializer` global] → Un array enviado a futuro se serializará repetido; es el formato que espera FastAPI.
- ["Sin cerrar" depende del reloj del navegador] → Igual que el resto del frontend (`parseHoraNegocio`); el backend no cambia de estado por esto.

## Migration Plan

No hay migración de datos. El despliegue es compatible: los parámetros nuevos son opcionales.
