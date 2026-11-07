# Spec Delta

## ADDED Requirements

### Requirement: Consulta de Disponibilidad (RF-TURNO-01)
El sistema DEBE permitir consultar slots disponibles de profesionales en un rango de fechas, con filtros opcionales por profesional y servicio.

#### Scenario: Consulta con filtros opcionales
- **WHEN** cliente consulta disponibilidad con fecha_inicio, fecha_fin, profesional_id opcional, servicio_id opcional
- **THEN** sistema retorna lista de profesionales con sus slots libres agrupados por fecha, filtrados según parámetros

#### Scenario: Consulta sin filtros
- **WHEN** cliente consulta disponibilidad solo con rango de fechas
- **THEN** sistema retorna todos los profesionales con slots libres en ese rango

#### Scenario: Profesional sin disponibilidad
- **WHEN** profesional no tiene slots libres en el rango consultado
- **THEN** sistema no incluye a ese profesional en la respuesta (o retorna lista vacía para él)

### Requirement: Reserva Manual por Cliente (RF-TURNO-02)
El sistema DEBE permitir a un cliente autenticado reservar un turno seleccionando profesional, servicio, fecha y hora.

#### Scenario: Reserva exitosa
- **WHEN** cliente autenticado selecciona profesional, servicio, fecha, hora libre y confirma
- **THEN** sistema crea turno en estado PENDIENTE que transiciona automáticamente a CONFIRMADO, y el slot ya no aparece como disponible

#### Scenario: Slot ya no disponible
- **WHEN** cliente intenta reservar un slot que fue tomado concurrentemente
- **THEN** sistema rechaza la reserva con error 409 Conflict indicando que el slot ya no está libre

#### Scenario: Servicio no pertenece al profesional
- **WHEN** cliente intenta reservar un servicio que no ofrece el profesional seleccionado
- **THEN** sistema rechaza la reserva con error 400 Bad Request

#### Scenario: Cliente no autenticado
- **WHEN** request sin token JWT válido intenta crear turno
- **THEN** sistema retorna 401 Unauthorized

### Requirement: Gestión de Turnos por Profesional (RF-TURNO-03)
El sistema DEBE permitir al profesional ver su grilla de turnos y gestionar sus estados.

#### Scenario: Grilla semanal con filtros
- **WHEN** profesional autenticado consulta sus turnos con filtros de fecha y estado
- **THEN** sistema retorna turnos del profesional coloreados por estado (PENDIENTE, CONFIRMADO, EN_CURSO, FINALIZADO, CANCELADO_CLIENTE, CANCELADO_PROVEEDOR, NO_ASISTIO)

#### Scenario: Cambio de estado válido
- **WHEN** profesional cambia estado CONFIRMADO → EN_CURSO → FINALIZADO secuencialmente
- **THEN** sistema actualiza estado y registra timestamp correspondiente (confirmado_en, finalizado_en)

#### Scenario: Cambio de estado inválido
- **WHEN** profesional intenta saltar estado (ej. PENDIENTE → FINALIZADO)
- **THEN** sistema rechaza con error 400 Bad Request indicando transición inválida

#### Scenario: Agregar nota interna
- **WHEN** profesional agrega/actualiza notas_profesional en un turno
- **THEN** sistema persiste la nota y la incluye en respuestas posteriores

### Requirement: Cancelación de Turno (RF-TURNO-04)
El sistema DEBE permitir cancelación por cliente (con antelación) y por profesional (cualquier momento futuro).

#### Scenario: Cancelación por cliente válida
- **WHEN** cliente cancela su turno futuro con >2 horas de antelación
- **THEN** sistema cambia estado a CANCELADO_CLIENTE, registra cancelado_por="cliente", motivo, cancelado_en, y libera el slot

#### Scenario: Cancelación por cliente tardía
- **WHEN** cliente intenta cancelar turno con ≤2 horas de antelación
- **THEN** sistema rechaza con error 400 Bad Request indicando que no cumple el plazo mínimo

#### Scenario: Cancelación por profesional
- **WHEN** profesional cancela turno futuro con motivo obligatorio
- **THEN** sistema cambia estado a CANCELADO_PROVEEDOR, registra cancelado_por="profesional", motivo, cancelado_en, y libera el slot

#### Scenario: Cancelación de turno pasado
- **WHEN** cualquiera intenta cancelar turno ya FINALIZADO o CANCELADO
- **THEN** sistema rechaza con error 400 Bad Request (solo turnos futuros)

### Requirement: Reasignación de Turno por Profesional (RF-TURNO-05)
El sistema DEBE permitir al profesional mover un turno a otro slot libre suyo.

#### Scenario: Reasignación exitosa
- **WHEN** profesional reasigna turno a nuevo slot libre suyo, mismo servicio (misma duración), turno futuro
- **THEN** sistema actualiza fecha y hora_inicio/hora_fin, registra auditoría con slot anterior/nuevo y motivo, mantiene estado

#### Scenario: Reasignación a slot ocupado
- **WHEN** profesional intenta reasignar a slot ya ocupado
- **THEN** sistema rechaza con error 409 Conflict

#### Scenario: Reasignación con servicio diferente
- **WHEN** profesional intenta reasignar a slot de distinta duración
- **THEN** sistema rechaza con error 400 Bad Request (debe ser mismo servicio)

### Requirement: Historial de Turnos (RF-TURNO-06)
El sistema DEBE proporcionar historial filtrado para cliente (solo propios) y profesional (todos los suyos).

#### Scenario: Historial cliente
- **WHEN** cliente autenticado consulta /turnos/mis-turnos con filtros de estado y fecha
- **THEN** sistema retorna solo sus turnos con estados correctos (PENDIENTE, CONFIRMADO, EN_CURSO, FINALIZADO, CANCELADO_CLIENTE, CANCELADO_PROVEEDOR, NO_ASISTIO)

#### Scenario: Historial profesional
- **WHEN** profesional autenticado consulta /profesionales/me/turnos con filtros avanzados
- **THEN** sistema retorna todos sus turnos con mismos estados y filtros

#### Scenario: Aislamiento de datos
- **WHEN** cliente A consulta turnos
- **THEN** sistema NUNCA retorna turnos de cliente B (enforced by query filter cliente_id = current_user.cliente_id)

### Requirement: Reserva por Chatbot - Endpoint Interno (RF-TURNO-07)
El sistema DEBE exponer endpoint interno para que el servicio de chatbot cree turnos.

#### Scenario: Reserva exitosa desde chatbot
- **WHEN** chatbot llama POST /internal/turnos/reservar con api key válida y datos (cliente_id, profesional_id, servicio_id, fecha, hora_inicio)
- **THEN** sistema valida igual que reserva manual, crea turno CONFIRMADO, retorna datos para respuesta conversacional

#### Scenario: API key inválida
- **WHEN** request a endpoint interno sin api key o key inválida
- **THEN** sistema retorna 401 Unauthorized

#### Scenario: Validaciones internas
- **WHEN** chatbot envía datos inválidos (slot ocupado, servicio no del profesional, etc.)
- **THEN** sistema retorna mismos errores que reserva manual (409, 400 según caso)

## REMOVED Requirements

### Requirement: Notificaciones automáticas (Email/WS)
**Reason**: Fuera de alcance para CU-03; se implementará en cambio futuro (CU-10)
**Migration**: Endpoint interno retorna datos necesarios; frontend/chatbot manejará notificaciones cuando se implemente