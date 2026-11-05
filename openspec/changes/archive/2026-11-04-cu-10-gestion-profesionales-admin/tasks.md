# Tasks: CU-10 Gestión de profesionales por el administrador

## 1. Regla de baja (backend)

- [x] 1.1 Cambiar `get_with_turnos_count` para contar turnos activos con `fecha_fin > ahora_negocio()`, extraer `ProfesionalService._validar_baja` y aplicarla en `desactivar_profesional` y en `actualizar_profesional` cuando `activo` pasa a `False`; traducir `ValueError` a 409 en `PUT`. Verificar: tests de API para baja por `PUT` con turno mañana (409), baja con turnos ya terminados hoy (204/200) y reactivar (200 y aparece en el listado público)

## 2. Tipos del frontend

- [x] 2.1 Alinear `Profesional`, `ProfesionalCreate` y `ProfesionalUpdate` en `types/index.ts` con la API y corregir los usos. Verificar: `npm run build`

## 3. Páginas del admin

- [x] 3.1 Crear `pages/admin/ProfesionalesPage.tsx` (lista, búsqueda, filtro, alta/edición en `Dialog`, desactivar con confirmación, reactivar) y su ruta. Verificar: `npm run build`
- [x] 3.2 Crear `pages/admin/TurnosPage.tsx` (lista paginada de solo lectura con filtros) y `pages/admin/DashboardPage.tsx` (contadores y accesos), con sus rutas. Verificar: `npm run build` y `npm run lint` sin errores

## 4. Verificación end-to-end

- [x] 4.1 En el navegador, como admin: crear un profesional, ver el error de email repetido, editarlo, intentar desactivar a Juan (con turnos) y ver el error, desactivar y reactivar al nuevo, iniciar sesión con el nuevo profesional y comprobar que no ve servicios ni grilla de otros, y filtrar "Todos los turnos" por Juan. Revisar las páginas a 375 px. Verificar: capturas
- [x] 4.2 Suite completa en verde y `ruff check app/` limpio. Verificar: `pytest` y `ruff check app/`

## Workflow follow-up

- `/opsx-archive` del change una vez implementado y revisado
- `mem_save` en Engram con las decisiones (regla de baja única)
