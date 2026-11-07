# Proposal: Rediseño completo de la interfaz

## Why

El frontend se armó caso de uso por caso de uso y hoy se nota:

- **Look genérico**: plantilla Tailwind índigo, sin sistema de diseño. Cada página repite clases sueltas (`text-3xl font-bold text-gray-900 dark:text-white`) y los colores de estado son amarillo/verde/rojo saturados.
- **Navegación que no escala**: header horizontal con hasta 6 ítems para el profesional; en pantallas medianas se rompe y pasa a menú hamburguesa.
- **Flujos confusos**:
  - El cliente tiene un único "Dashboard" con pestañas; `/cliente/reservar` y `/cliente/mis-turnos` renderizan la misma página, y el menú enlaza a `/cliente/perfil`, que no existe.
  - La reserva muestra profesional, servicio, fecha y horario todos juntos, sin pasos ni resumen antes de confirmar.
  - El profesional no tiene una vista de "hoy": para atender tiene que ir a la grilla semanal y buscar el turno.
  - El admin ve dos números sueltos como dashboard.
- **Modo oscuro a medias**: hay clases `dark:` pero no hay toggle ni tokens.
- **Sin landing**: quien entra sin sesión cae directo en el login.

## What Changes

- **Sistema de diseño clínico/profesional**: tokens CSS (colores, tipografía, radios, sombras) con tema claro y oscuro; azul `#1D4ED8` como acento, neutros fríos, tipografía Inter, iconos lineales (lucide). Componentes base reescritos: Button, Input, Select, Card, Badge, Dialog, Tabs, Table, EmptyState, Skeleton, Toast.
- **Toggle de tema** claro / oscuro / sistema, persistido en `localStorage`.
- **Nuevo shell**: sidebar lateral colapsable por rol (barra inferior en mobile), cabecera de página con título, descripción y acciones.
- **Landing pública** (`/`) para visitantes: propuesta de valor, cómo funciona y accesos a login/registro. Login y registro con layout de dos columnas.
- **Cliente**:
  - Inicio con el próximo turno destacado y accesos rápidos.
  - **Reserva en 4 pasos** (`/cliente/reservar`): profesional → servicio → fecha y hora → confirmar, con resumen lateral persistente.
  - Mis turnos (`/cliente/mis-turnos`) como página propia, con próximos/pasados.
  - Asistente virtual como burbuja flotante abajo a la derecha que abre una ventana de chat, rediseñada con el nuevo sistema.
  - Se quita el enlace a `/cliente/perfil` (no existe backend para eso).
- **Profesional**:
  - **Hoy** (nuevo inicio): agenda del día en línea de tiempo con acciones rápidas (confirmar, iniciar, finalizar, ausente).
  - Agenda semanal rediseñada (grilla con colores de estado sobrios).
  - Historial, Servicios, Disponibilidad y Perfil con el nuevo sistema; Servicios, Disponibilidad y Perfil agrupados bajo "Configuración".
- **Reserva sin cuenta**: un visitante puede recorrer la reserva (`/reservar`) sin registrarse. Al confirmar se le pide crear cuenta o iniciar sesión, y después vuelve al paso de confirmación con el turno que había elegido.
- **Admin**: resumen con métricas (profesionales activos/inactivos, turnos de hoy por estado), tabla de turnos con filtros y gestión de profesionales en tabla.

## Capabilities

### New Capabilities
- `frontend`: sistema de diseño, navegación por rol y flujos de pantalla.

### Modified Capabilities
- `turnos`: la consulta de disponibilidad es pública (ya lo decía RF-TURNO-01: "Público/Cliente"). Reservar sigue requiriendo cuenta de cliente.
- `profesionales`: el listado y detalle públicos responden sin sesión.

## Impact

- **Frontend**: reescritura de `src/components/**`, `src/pages/**`, `src/App.tsx`, `src/index.css`. Se borran `App.css` y los assets del template de Vite. Se mantienen `services/api.ts`, `types/index.ts`, `contexts/AuthContext.tsx`, `utils/*` y `components/turnos/estado.ts` (solo cambian los colores).
- **Dependencias**: ninguna nueva. Inter se carga desde Google Fonts.
- **Backend**: `api/v1/profesionales_public.py` y `api/v1/turnos.py` (disponibilidad) usan sesión opcional; tests en `tests/api/v1/test_turnos.py` y `tests/api/v1/test_profesionales_public.py`.

## Fuera de alcance

- Perfil de cliente editable.
- Notificaciones, i18n, PWA.
