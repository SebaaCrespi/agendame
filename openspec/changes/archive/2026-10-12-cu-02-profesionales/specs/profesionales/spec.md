# Spec Delta

## Purpose

Implementa la capa backend completa para gestión de profesionales, servicios, disponibilidad horaria (grilla semanal + excepciones) y generación de slots disponibles, según los specs principales en `openspec/specs/profesionales/`.

## ADDED Requirements

### Requirement: API Response Format Consistency
Todas las respuestas de la API DEBEN seguir un formato consistente con paginación, metadatos y códigos de error RFC 7807.

#### Scenario: Listado paginado exitoso
- **WHEN** cliente solicita `GET /admin/profesionales?page=1&size=20`
- **THEN** respuesta 200 con cuerpo `{items: [...], total: 42, page: 1, size: 20, pages: 3}`

#### Scenario: Error de validación en creación
- **WHEN** cliente envía `POST /admin/profesionales` con email duplicado
- **THEN** respuesta 409 con formato RFC 7807 `{type, title: "Conflict", status: 409, detail: "Email ya registrado", instance: "/admin/profesionales"}`

### Requirement: Validación de Integridad Referencial
El sistema DEBE garantizar integridad referencial entre User, Profesional, Servicio, Disponibilidad y ExcepcionDisponibilidad mediante constraints de BD y cascada.

#### Scenario: Eliminación en cascada de profesional
- **WHEN** admin elimina profesional con servicios, disponibilidad y excepciones asociadas
- **THEN** se eliminan en cascada: servicios, disponibilidades, excepciones (soft delete del profesional)

#### Scenario: Prevención de huérfanos
- **WHEN** se intenta crear servicio sin profesional_id válido
- **THEN** BD rechaza con error FK

### Requirement: Paginación y Filtros Estándar
Todos los endpoints de listado DEBEN soportar paginación (`page`, `size` con defaults y máximos) y filtros declarativos.

#### Scenario: Filtros combinados en listado admin
- **WHEN** admin solicita `GET /admin/profesionales?activo=true&q=maria&page=2&size=10`
- **THEN** retorna página 2 de 10, filtrando por nombre que contiene "maria" y solo activos

#### Scenario: Límite máximo de página
- **WHEN** cliente solicita `GET /profesionales?size=200`
- **THEN** respuesta usa size=50 (máximo configurado) y retorna metadatos con size=50

### Requirement: Aislamiento de Datos por Profesional (RBAC)
El sistema DEBE garantizar que un profesional solo acceda a SUS recursos (servicios, disponibilidad, excepciones, slots).

#### Scenario: Profesional accede a sus servicios
- **WHEN** profesional autenticado solicita `GET /profesionales/me/servicios`
- **THEN** retorna solo servicios donde `servicio.profesional_id == current_user.profesional.id`

#### Scenario: Profesional intenta acceder a servicio ajeno
- **WHEN** profesional autenticado solicita `PUT /profesionales/me/servicios/999` (ID ajeno)
- **THEN** respuesta 404 (no 403 para no revelar existencia)

#### Scenario: Admin ve todos los servicios
- **WHEN** admin solicita `GET /admin/profesionales/1/servicios`
- **THEN** retorna todos los servicios del profesional ID 1

### Requirement: Generación Determinística de Slots
El sistema DEBE generar slots disponibles de forma determinística basada en grilla semanal, excepciones y turnos existentes.

#### Scenario: Slots excluyen turnos confirmados
- **WHEN** profesional tiene grilla Lun-Vie 9-13 y turno confirmado 2026-10-15 10:00-10:30
- **THEN** `GET /profesionales/1/slots?desde=2026-10-15&hasta=2026-10-15` NO incluye slot 10:00-10:30

#### Scenario: Excepciones tienen prioridad sobre grilla
- **WHEN** grilla dice Viernes 9-13, pero excepción 2026-10-17 dice "cerrado"
- **THEN** slots para 2026-10-17 están vacíos (día cerrado)

#### Scenario: Duración de slot = MCM(duración servicios) o slot_duracion_min
- **WHEN** profesional tiene servicios de 30min y 45min, slot_duracion_min=15
- **THEN** slots generados cada 15min (MCM de 30 y 45 = 90, pero slot_duracion_min=15 gana)

### Requirement: Validación de Duración y Precio de Servicios
Los servicios DEBEN validar duración positiva y precio no negativo a nivel API y BD.

#### Scenario: Duración inválida rechazada
- **WHEN** profesional crea servicio con `duracion_min: 0`
- **THEN** respuesta 422 con detalle "duracion_min debe ser mayor a 0"

#### Scenario: Precio negativo rechazado
- **WHEN** profesional actualiza servicio con `precio: -10`
- **THEN** respuesta 422 con detalle "precio debe ser >= 0"

### Requirement: Nombre de Servicio Único por Profesional
El sistema DEBE garantizar unicidad de nombre de servicio por profesional (case-insensitive).

#### Scenario: Nombre duplicado rechazado
- **WHEN** profesional crea servicio "Corte" y ya tiene "corte"
- **THEN** respuesta 409 "Nombre de servicio ya existe para este profesional"

### Requirement: Excepciones Tienen Prioridad Sobre Grilla Semanal
Las excepciones de disponibilidad DEBEN sobrescribir la grilla semanal para fechas específicas.

#### Scenario: Excepción "cerrado" anula día laboral
- **WHEN** grilla dice Sábado 9-13, excepción 2026-12-25 hora_inicio=NULL
- **THEN** `GET /profesionales/1/slots?desde=2026-12-25&hasta=2026-12-25` retorna items=[]

#### Scenario: Excepción con horario personalizado
- **WHEN** grilla dice Lunes 9-13, excepción 2026-11-02 hora_inicio=10:00, hora_fin=14:00
- **THEN** slots para 2026-11-02 son 10:00-10:30, 10:30-11:00... (no 9:00-9:30)

### Requirement: Soft Delete de Profesional con Validación de Turnos Futuros
El sistema DEBE permitir desactivar profesional solo si no tiene turnos futuros confirmados/pendientes.

#### Scenario: Desactivación exitosa sin turnos futuros
- **WHEN** admin desactiva profesional sin turnos futuros
- **THEN** profesional.activo=false, usuario asociado permanece (para historial)

#### Scenario: Desactivación bloqueada con turnos futuros
- **WHEN** admin intenta desactivar profesional con turno CONFIRMADO mañana
- **THEN** respuesta 409 "No se puede desactivar: tiene 3 turnos futuros confirmados"

### Requirement: Slot Duration Configurable por Profesional
Cada profesional DEBE poder configurar su `slot_duracion_min` (default 30) que define la granularidad base de slots.

#### Scenario: Slot duration personalizada
- **WHEN** profesional configura `slot_duracion_min: 20` y tiene servicios 40min
- **THEN** slots generados cada 20min (0:00, 0:20, 0:40...), servicio ocupa 2 slots

## MODIFIED Requirements

### Requirement: RF-PROF-01: CRUD de Profesionales (Admin)
**Cambio**: Agregar validación de email único a nivel usuario (no solo profesional) y creación automática de usuario PROVEEDOR.

#### Scenario: Creación automática de usuario PROVEEDOR
- **WHEN** admin crea profesional con email nuevo
- **THEN** se crea User con rol=PROVEEDOR, email=profesional.email, password temporal, y Professional vinculado

#### Scenario: Email duplicado en usuario
- **WHEN** admin crea profesional con email que ya existe en users
- **THEN** respuesta 409 "Email ya registrado en el sistema"

## REMOVED Requirements

### Requirement: RF-PROF-03b: Generación de Slots con MCM automático
**Reason**: Simplificación - usar `slot_duracion_min` configurable en lugar de calcular MCM automáticamente de duraciones de servicios, que generaba confusión y slots muy fragmentados.
**Migration**: Profesional configura `slot_duracion_min` (default 30). Frontend sugiere valor basado en MCM de sus servicios.