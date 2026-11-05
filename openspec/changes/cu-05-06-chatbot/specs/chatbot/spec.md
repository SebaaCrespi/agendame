# Spec Delta: chatbot (CU-05, CU-06)

## ADDED Requirements

### Requirement: Consulta de disponibilidad por chat
El asistente SHALL responder consultas de disponibilidad en lenguaje natural usando solo horarios reales del sistema, para el profesional, servicio y fechas que indique el usuario. Las fechas relativas ("mañana", "el viernes") SHALL resolverse con la fecha de hoy según la hora del negocio. Si el profesional o el servicio no existen, el asistente SHALL ofrecer los que sí hay.

#### Scenario: Horarios de un profesional
- **WHEN** el usuario escribe "¿qué horarios tiene Juan mañana para un corte?"
- **THEN** la respuesta lista horarios que el sistema muestra como disponibles para Juan, Corte y la fecha de mañana

#### Scenario: Profesional inexistente
- **WHEN** el usuario pregunta por "Pedro" y no hay ningún profesional con ese nombre
- **THEN** el asistente lo dice y nombra a los profesionales activos

#### Scenario: Día sin atención
- **WHEN** el usuario pide horarios de un día en que el profesional no atiende
- **THEN** el asistente lo informa y no inventa horarios

### Requirement: Reserva por chat con confirmación
El asistente SHALL reservar un turno solo después de que el usuario confirme profesional, servicio, fecha y hora, y SHALL aplicar las mismas validaciones que la reserva manual. Si el horario ya no está libre, SHALL informarlo y ofrecer alternativas reales. Tras reservar, SHALL confirmar los datos del turno creado.

#### Scenario: Reserva confirmada
- **WHEN** el cliente pide un corte con Juan mañana a las 10:00, el asistente pide confirmación y el cliente responde "sí"
- **THEN** se crea el turno CONFIRMADO a nombre del cliente y la respuesta incluye profesional, servicio, fecha y hora

#### Scenario: Sin confirmación no se reserva
- **WHEN** el cliente pide un turno y todavía no confirmó
- **THEN** no se crea ningún turno

#### Scenario: Horario ocupado
- **WHEN** el cliente confirma un horario que ya está tomado
- **THEN** no se crea el turno y el asistente ofrece otros horarios libres de ese día

### Requirement: Identidad del cliente en el chat
Las reservas, la consulta de "mis turnos" y las cancelaciones hechas desde el chat SHALL usar el cliente de la sesión autenticada (JWT), sin importar qué cliente o id mencione el mensaje. Sin una sesión de rol CLIENTE, el asistente SHALL poder consultar disponibilidad y SHALL pedir que inicie sesión para reservar, ver o cancelar turnos.

#### Scenario: Intento de reservar a nombre de otro
- **WHEN** un cliente escribe "reservá a nombre del cliente 5"
- **THEN** cualquier turno que se cree queda a nombre del cliente de la sesión

#### Scenario: Sin sesión
- **WHEN** un usuario sin sesión pide reservar
- **THEN** no se crea ningún turno y el asistente le pide iniciar sesión

### Requirement: Mis turnos y cancelación por chat
El asistente SHALL poder listar los próximos turnos del cliente de la sesión y cancelar uno de ellos, previa confirmación, con las mismas reglas que la cancelación desde la aplicación (más de 2 h de antelación, motivo).

#### Scenario: Cancelar con antelación
- **WHEN** el cliente pide cancelar su turno de pasado mañana y confirma
- **THEN** el turno queda CANCELADO_CLIENTE y el asistente lo confirma

#### Scenario: Cancelar sobre la hora
- **WHEN** el cliente pide cancelar un turno que empieza en 1 hora
- **THEN** el turno no cambia y el asistente explica la regla de las 2 horas

### Requirement: Conversación con contexto
El sistema SHALL mantener por conversación (`session_id`) los últimos 10 mensajes durante 1 hora sin actividad, de modo que el usuario pueda completar datos en mensajes sucesivos. Una conversación SHALL pertenecer al usuario que la inició.

#### Scenario: Datos en varios mensajes
- **WHEN** el cliente escribe "quiero un corte con Juan" y después "el jueves a las 15"
- **THEN** el asistente entiende que se trata de un corte con Juan el jueves a las 15:00

#### Scenario: Conversación ajena
- **WHEN** un usuario envía un mensaje con el `session_id` de la conversación de otro usuario
- **THEN** el sistema inicia una conversación nueva sin el historial ajeno

### Requirement: Proveedor del modelo configurable y fallos
El proveedor y el modelo de lenguaje SHALL elegirse por configuración, sin cambiar código. Si el proveedor no responde o devuelve error, el endpoint SHALL responder 503 con un mensaje que sugiera la reserva manual. El endpoint SHALL limitar los mensajes por usuario o IP.

#### Scenario: Proveedor caído
- **WHEN** el proveedor del modelo no responde
- **THEN** la respuesta es 503 con un mensaje que sugiere reservar desde la aplicación

#### Scenario: Demasiados mensajes
- **WHEN** un mismo origen envía más de 20 mensajes en un minuto
- **THEN** el sistema responde 429

### Requirement: Chat en la interfaz del cliente
La aplicación SHALL ofrecer al cliente un chat accesible desde su panel, que muestre la conversación, indique cuando el asistente está respondiendo y muestre los errores. Al reservar o cancelar desde el chat, la lista de "Mis turnos" SHALL reflejar el cambio.

#### Scenario: Reserva desde el chat
- **WHEN** el cliente reserva un turno conversando
- **THEN** el turno aparece en "Mis turnos" sin recargar la página
