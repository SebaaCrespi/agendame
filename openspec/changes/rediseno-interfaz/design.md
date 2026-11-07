# Design: Rediseño completo de la interfaz

## Principios

1. **Clínico y legible**: fondo blanco, un solo acento azul, mucho aire. El color se reserva para estados y acciones.
2. **Una tarea por pantalla**: cada ruta resuelve una cosa; nada de pestañas que esconden páginas.
3. **Lo urgente primero**: el inicio de cada rol muestra lo que hay que hacer ahora (próximo turno, agenda de hoy, turnos del día).
4. **Accesible**: contraste AA, foco visible, objetivos táctiles ≥ 40px, `aria-*` en navegación y diálogos.

## Decisión 1: Tokens CSS + Tailwind v4 `@theme`

El proyecto ya usa Tailwind v4 (`@import "tailwindcss"`). Se definen variables en `:root` y `[data-theme="dark"]` y se exponen con `@theme inline` para usarlas como utilidades (`bg-surface`, `text-muted`, `border-line`, `bg-primary`).

| Token | Claro | Oscuro |
|-------|-------|--------|
| `--bg` | `#F8FAFC` | `#0B1120` |
| `--surface` | `#FFFFFF` | `#111827` |
| `--surface-2` | `#F1F5F9` | `#1F2937` |
| `--line` | `#E2E8F0` | `#1F2A3C` |
| `--text` | `#0F172A` | `#E5E7EB` |
| `--muted` | `#64748B` | `#94A3B8` |
| `--primary` | `#1D4ED8` | `#3B82F6` |
| `--primary-soft` | `#EFF6FF` | `rgba(59,130,246,.14)` |
| `--success` / `--warning` / `--danger` | `#047857` / `#B45309` / `#B91C1C` | `#34D399` / `#FBBF24` / `#F87171` |

Tipografía: Inter 400/500/600, escala 12/14/16/20/24/30. Radios 8px (controles) y 12px (cards). Sombras mínimas; la separación se hace con bordes.

Alternativa descartada: seguir con clases `gray-*`/`dark:` sueltas. Duplica cada color y no permite toggle manual.

## Decisión 2: Tema con `data-theme` en `<html>`

`ThemeProvider` guarda `light | dark | system` en `localStorage` y aplica `data-theme`. Un script inline en `index.html` lo aplica antes del primer render para evitar el parpadeo. Tailwind usa `@custom-variant dark` sobre `[data-theme=dark]`.

## Decisión 3: Shell con sidebar por rol

`AppShell` = sidebar (240px, colapsable a 64px en desktop; barra inferior con los 4 ítems principales en < 768px) + área de contenido con `PageHeader`. La navegación se define en un único `nav.ts` por rol:

- **Cliente**: Inicio · Reservar · Mis turnos (el asistente es la burbuja flotante)
- **Profesional**: Hoy · Agenda · Historial · Configuración (Servicios, Disponibilidad, Perfil)
- **Admin**: Resumen · Turnos · Profesionales

El pie del sidebar muestra el usuario, el toggle de tema y "Salir".

## Decisión 4: Reserva como wizard con estado en URL

`/cliente/reservar?prof=&serv=&fecha=&hora=`: cada paso escribe en los query params, así el botón "atrás" del navegador funciona y se puede compartir/recargar. Resumen lateral (abajo en mobile) con lo elegido y botón Confirmar en el paso 4. Tras confirmar: pantalla de éxito con "Ver mis turnos" y "Reservar otro".

Los datos vienen de los mismos endpoints que hoy (`getProfesionalesPublic`, `consultarDisponibilidad`, `crearReserva`).

## Decisión 5: Vista "Hoy" del profesional

Lista cronológica de los turnos del día (`getMisTurnosProfesional` con `desde=hasta=hoy`), con indicador de "ahora", el turno en curso destacado y botones de transición según `TRANSICIONES`. Reutiliza `TurnoDetallePanel`, `CancelarDialog` y `ReasignarDialog` con el nuevo estilo.

## Decisión 6: Asistente como burbuja flotante

`ChatWidget` se mantiene como burbuja fija abajo a la derecha (en mobile, por encima de la barra inferior) que abre una ventana de chat. Se rediseña con los tokens nuevos: cabecera con estado, mensajes en burbujas, sugerencias rápidas y campo de texto fijo. En mobile la ventana ocupa casi toda la pantalla. Mantiene la sesión en `sessionStorage` como hoy y se muestra solo al cliente.

## Decisión 7: Colores de estado sobrios

Badges con fondo suave y punto de color en lugar de bloques saturados; cancelados en gris tachado. La grilla semanal usa una barra lateral de 3px del color del estado sobre fondo `surface`.

## Riesgos

- **Reescritura grande sin tests de frontend**: se valida con `npm run build`, `npm run lint` y recorrido manual de cada rol en el navegador con el seed (`backend/scripts/seed_dev.py`).
- **Rutas cambiadas**: `/cliente/dashboard` y `/profesional/dashboard` redirigen al nuevo inicio para no romper enlaces.
