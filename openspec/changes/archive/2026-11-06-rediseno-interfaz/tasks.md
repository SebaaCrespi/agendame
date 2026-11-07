# Tasks: Rediseño completo de la interfaz

## 1. Sistema de diseño

- [x] 1.1 Tokens en `src/index.css` (`:root`, `[data-theme=dark]`, `@theme inline`, `@custom-variant dark`) + Inter en `index.html`. Borrar `App.css` y assets del template. Verificar: `npm run build`
- [x] 1.2 `ThemeProvider` + script anti-parpadeo + `ThemeToggle`. Verificar: el tema sobrevive a recargar
- [x] 1.3 Reescribir `components/ui`: Button, Input, Select, Textarea, Card, Badge, Dialog, Tabs, Table, EmptyState, Skeleton, Toast, Alerta, Paginacion. Verificar: build + lint
- [x] 1.4 Colores de estado sobrios en `components/turnos/estado.ts` + componente `EstadoBadge`

## 2. Shell y rutas

- [x] 2.1 `AppShell` (sidebar colapsable, barra inferior mobile), `PageHeader`, `nav.ts` por rol
- [x] 2.2 Rutas nuevas en `App.tsx` con redirecciones desde las viejas (`/cliente/dashboard`, `/profesional/dashboard`)
- [x] 2.3 Landing pública en `/` y layout de auth de dos columnas para Login y Registro

## 3. Cliente

- [x] 3.1 Inicio: próximo turno destacado + accesos rápidos
- [x] 3.2 Wizard de reserva en 4 pasos con estado en query params, resumen lateral, éxito y manejo de 409
- [x] 3.3 Página Mis turnos (próximos/pasados, cancelar)
- [x] 3.4 Burbuja flotante del asistente rediseñada (`ChatWidget`)

## 4. Profesional

- [x] 4.1 Vista Hoy con línea de tiempo y acciones de estado
- [x] 4.2 Agenda semanal (WeekGrid restilizada) + panel de detalle, cancelar y reasignar
- [x] 4.3 Historial con filtros y tabla
- [x] 4.4 Configuración: Servicios, Disponibilidad, Perfil

## 5. Admin

- [x] 5.1 Resumen con métricas
- [x] 5.2 Turnos (tabla + filtros) y Profesionales (tabla + alta/edición/baja)

## 6. Verificación

- [x] 6.1 `npm run build` y `npm run lint` sin errores
- [x] 6.2 Recorrido en navegador con el seed: los tres roles, claro y oscuro, desktop y 375px

## 7. Reserva sin cuenta

- [x] 7.1 Tests: visitante consulta profesionales y disponibilidad (200), reservar sin login (401), token inválido (401)
- [x] 7.2 Backend: `get_current_user_optional` en endpoints públicos de profesionales y en disponibilidad. Verificar: `pytest` completo en verde
- [x] 7.3 Frontend: ruta pública `/reservar`, "Crear cuenta y reservar" / "Ya tengo cuenta" en el paso 4, `?next=` seguro en login y registro, aviso al retomar
- [x] 7.4 Recorrido en navegador: visitante → registro → confirmar, y visitante → login → confirmar
