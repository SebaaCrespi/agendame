# Tasks: CU-07 Gestión de grilla y turnos asignados

## 1. Datos legibles del turno

- [x] 1.1 Agregar al modelo `Turno` las propiedades `cliente_nombre`, `cliente_telefono`, `servicio_nombre` y `profesional_nombre`, y sumarlas a `TurnoResponse`. Verificar: tests de API de que `GET /profesionales/me/turnos` y `GET /turnos/mis-turnos` incluyen los nombres, y también la respuesta de `POST /turnos` recién creado

## 2. Filtros del proveedor

- [x] 2.1 `TurnoFiltros` suma `servicio_id` y `cliente`; `TurnoRepo.get_by_profesional` los aplica (join a `User` con `lower().contains`); el endpoint `GET /profesionales/me/turnos` los expone como query params. Verificar: tests de API para filtro por servicio, por cliente (sin distinguir mayúsculas), combinados, y con un servicio de otro profesional (lista vacía)

## 3. Marcar ausencia

- [x] 3.1 Agregar CONFIRMADO → NO_ASISTIO a `TRANSICIONES_VALIDAS`, condicionado en `cambiar_estado` a que la hora de inicio ya haya pasado según `ahora_negocio()` (si no, 422). Verificar: tests de servicio con reloj parcheado, antes y después de la hora, y test de API `PUT /estado` → 422

## 4. Frontend: base

- [x] 4.1 Crear `RoleRedirect` en `App.tsx` para `/` y `*`, y sumar las rutas reales del proveedor (`dashboard` y `turnos`). Verificar: `npm run build`, y en el navegador el login de `juan@agendame.com` llega a `/profesional/dashboard` sin loop
- [x] 4.2 Crear `utils/horaNegocio.ts` (`parseHoraNegocio`, `formatHora`) y usarlo en las tarjetas de "Mis turnos" del cliente. Agregar a `types/index.ts` los campos nuevos de `Turno` y los filtros, y a `api.ts` los params de `getMisTurnosProfesional`. Verificar: `npm run build`

## 5. Frontend: grilla y detalle

- [x] 5.1 Crear `components/turnos/WeekGrid.tsx` (7 columnas, eje de horas según la grilla del profesional con fallback 08–20, bloques coloreados por estado, scroll horizontal propio en pantallas angostas). Verificar: `npm run build` y revisión visual en el navegador
- [x] 5.2 Crear `pages/profesional/TurnosPage.tsx` con navegación de semanas, filtros (estado, servicio, cliente) y `components/turnos/TurnoDetallePanel.tsx` con las transiciones válidas y la edición de notas, mostrando el `detail` del backend cuando hay error. Verificar: `npm run build` y `npm run lint` sin errores
- [x] 5.3 Crear `pages/profesional/DashboardPage.tsx` con los turnos de hoy, el conteo por estado y un enlace a la grilla. Verificar: `npm run build`

## 6. Verificación end-to-end

- [x] 6.1 Agregar al seed algunos turnos de ejemplo para Juan en la semana actual (idempotente). Verificar: correrlo dos veces no duplica turnos
- [x] 6.2 En el navegador, como `juan@agendame.com`: login → dashboard → grilla de la semana → filtrar por servicio y por cliente → abrir un turno → CONFIRMADO → EN_CURSO → FINALIZADO → editar las notas → navegar de semana. Verificar con un ancho de 375 px que la página no scrollea horizontalmente. Verificar: capturas del flujo
- [x] 6.3 Suite completa en verde y `ruff check app/` limpio. Verificar: `pytest` y `ruff check app/`

## Workflow follow-up

- `/opsx-archive` del change una vez implementado y revisado
- `mem_save` en Engram con las decisiones (propiedades de nombres, `parseHoraNegocio`, ausencia condicionada por la hora)
