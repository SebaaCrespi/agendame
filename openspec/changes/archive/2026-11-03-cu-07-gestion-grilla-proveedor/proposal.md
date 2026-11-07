# Proposal: CU-07 Gestión de grilla y turnos asignados

## Why

CU-07 pide que el proveedor pueda ver, filtrar y administrar los turnos de su grilla. La API ya expone `/profesionales/me/turnos` (listar, detalle, cambiar estado, notas), pero el proveedor no puede usarla desde la aplicación:

- Al iniciar sesión, un PROVEEDOR entra en un loop de redirecciones: `/` lleva a `/cliente/dashboard`, que no le corresponde y lo devuelve a `/`. Nunca llega a su panel.
- Todas las pantallas del proveedor son placeholders ("Próximamente").
- La respuesta de un turno solo trae ids, así que la grilla no puede mostrar quién es el cliente ni qué servicio reservó.
- El listado solo filtra por estado y fecha; el spec de turnos (RF-TURNO-03) pide también filtrar por cliente y por servicio.
- Un cliente que no se presenta no se puede marcar como NO_ASISTIO: la matriz de estados solo lo permite desde EN_CURSO, un estado al que ese turno nunca llega.

## What Changes

- **Redirección por rol**: la ruta inicial lleva a cada usuario al panel de su rol.
- **Datos legibles del turno**: las respuestas de turnos incluyen el nombre del cliente, del servicio y del profesional, y el teléfono del cliente.
- **Filtros del listado del proveedor**: se suman `servicio_id` y `cliente` (búsqueda por nombre), además de estado y rango de fechas.
- **Ausente**: un turno CONFIRMADO se puede marcar como NO_ASISTIO una vez pasada su hora de inicio (hora del negocio).
- **Pantalla "Mis turnos" del proveedor**: grilla semanal (lunes a domingo, con navegación entre semanas) con los turnos coloreados por estado, filtros, y un panel de detalle para cambiar el estado (solo a las transiciones válidas) y editar las notas internas.
- **Dashboard del proveedor**: resumen de los turnos de hoy y acceso a la grilla.

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `turnos`: las respuestas de turnos incluyen datos legibles; el listado del proveedor filtra por servicio y cliente; CONFIRMADO → NO_ASISTIO permitido después de la hora de inicio.

## Impact

- **Backend**: `schemas/turno.py`, `repositories/turno_repo.py`, `services/turno_service.py`, `api/v1/profesionales_me.py`.
- **Frontend**: `App.tsx` (redirección por rol y rutas), nuevas páginas `pages/profesional/DashboardPage.tsx` y `pages/profesional/TurnosPage.tsx`, componentes en `components/turnos/`, y `services/api.ts` / `types/index.ts`.
- **Tests**: servicio y API de turnos (filtros, datos legibles, NO_ASISTIO).
- **API**: solo se agregan campos y parámetros opcionales, así que no rompe a ningún consumidor.

## Fuera de alcance

- Cancelación y reasignación desde la interfaz del proveedor (CU-08). El backend ya las soporta.
- Historial con vista de lista paginada (CU-09).
- Pantallas de perfil, servicios y disponibilidad del proveedor (frontend de CU-02).
- Vista mensual; notificaciones.
