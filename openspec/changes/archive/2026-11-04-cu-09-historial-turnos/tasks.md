# Tasks: CU-09 Consulta de historial de turnos

## 1. Filtros del backend

- [x] 1.1 Cambiar `TurnoFiltros.estado` a lista de `TurnoEstado`, agregar el enum `MomentoTurno` y el campo `momento`, y declarar `estado` (repetible) y `momento` en `GET /turnos/mis-turnos` y `GET /profesionales/me/turnos`. Verificar: `momento=ayer` y `estado=BORRADO` → 422 en tests de API
- [x] 1.2 Aplicar estado (`in_`) y momento (filtro por `fecha_fin` contra `ahora_negocio()` y orden) en `get_by_cliente` y `get_by_profesional` con un helper común. Verificar: tests de repositorio/servicio con el reloj parcheado para próximos (incluye un turno en curso), pasados (orden descendente), varios estados con el total correcto, y sin `momento` el orden actual

## 2. Cliente API y tipos

- [x] 2.1 Configurar `paramsSerializer: { indexes: null }` en axios y actualizar `TurnoFiltros` en `types/index.ts` (`estado` como lista, `momento`). Ajustar `TurnosPage` al nuevo tipo. Verificar: `npm run build`

## 3. Historial del cliente

- [x] 3.1 En `DashboardPage` agregar pestañas Próximos/Pasados, grupo de estado y desde/hasta; cargar con `useEffect` sobre los filtros; mostrar `profesional_nombre`, `servicio_nombre`, estado legible, motivo de cancelación y reasignación. Verificar: `npm run build` y `npm run lint` sin errores

## 4. Historial del proveedor

- [x] 4.1 Crear `pages/profesional/HistorialPage.tsx` (lista paginada, filtros momento/estado/fechas/servicio/cliente, marca "Sin cerrar", detalle con `TurnoDetallePanel`), la ruta `/profesional/historial` y el ítem "Historial" del menú. Verificar: `npm run build` y `npm run lint` sin errores

## 5. Verificación end-to-end

- [x] 5.1 En el navegador:
  - Como cliente: ver Próximos y Pasados, filtrar Cancelados (con motivo), comprobar nombres de profesional y servicio, y pasar de página.
  - Como Juan: abrir Historial, filtrar un rango de varias semanas por servicio, encontrar un turno "Sin cerrar" y marcarlo ausente desde el detalle.
  - Revisar ambas vistas a 375 px.

  Verificar: capturas
- [x] 5.2 Suite completa en verde y `ruff check app/` limpio. Verificar: `pytest` y `ruff check app/`

## Workflow follow-up

- `/opsx-archive` del change una vez implementado y revisado
- `mem_save` en Engram con las decisiones (`estado` repetible, `momento` por `fecha_fin`)
