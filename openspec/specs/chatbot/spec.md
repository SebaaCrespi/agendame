# Especificación de Dominio: Chatbot / Asistente Virtual (CU-05, CU-06)

## Purpose

Asistente conversacional integrado (LangChain + Groq API) para consulta de disponibilidad y agendamiento de turnos por lenguaje natural. Expone herramientas (tools/functions) que el LLM invoca para interactuar con el backend.

## Arquitectura

```
Usuario (Frontend Chat) 
    ↓ WebSocket / REST
Backend FastAPI (Chatbot Service)
    ↓ LangChain Agent (ReAct / OpenAI Functions)
Groq API (LLM: openai/gpt-oss-120b)
    ↓ Tool Calling
Backend Internal APIs (Profesionales, Turnos, Disponibilidad)
```

## Requisitos Funcionales

### RF-CHAT-01: Consulta de Disponibilidad por Lenguaje Natural (CU-05)
- **Entrada**: Mensaje usuario ej. *"¿Qué horarios tiene Juan el martes que viene?"*
- **Proceso**:
  1. LLM identifica intención: `consultar_disponibilidad`
  2. Extrae entidades: profesional (nombre/id), fecha/rango, servicio (opcional)
  3. Invoca tool `buscar_slots_disponibles(profesional_id, fecha_inicio, fecha_fin)`
  4. Formatea respuesta conversacional con slots agrupados por día
- **Salida**: *"Juan tiene disponibles el martes 15: 10:00, 10:30, 11:00, 15:00, 15:30. ¿Te interesa alguno?"*

### RF-CHAT-02: Agendamiento por Lenguaje Natural (CU-06)
- **Entrada**: *"Quiero reservar corte con Juan el martes a las 10:30"*
- **Proceso**:
  1. LLM identifica intención: `reservar_turno`
  2. Extrae: profesional, servicio, fecha, hora
  3. Valida slot disponible (tool `verificar_slot`)
  4. Si cliente no identificado → pide login/registro
  5. Invoca tool `crear_turno(cliente_id, profesional_id, servicio_id, fecha, hora)`
  6. Confirma con detalles
- **Salida**: *"¡Listo! Tu corte con Juan el martes 15 a las 10:30 está confirmado. Duración: 30 min. Te esperamos."*

### RF-CHAT-03: Contexto de Conversación
- **Memoria**: Mantener contexto de sesión (últimos 10 mensajes)
- **Entidades persistentes**: Profesional actual, servicio actual, fechas mencionadas
- **Clarificación**: Si faltan datos → pregunta dirigida (*"¿Para qué servicio?"*, *"¿Qué día prefieres?"*)

### RF-CHAT-04: Manejo de Errores y Fallbacks
- **Slot no disponible**: *"Ese horario ya no está libre. Disponibles: 10:00, 11:00..."*
- **Profesional no encontrado**: *"No encuentro a 'Juan'. Tenemos: María (corte), Carlos (barba)..."*
- **Fuera de horario**: *"Juan atiende de 9 a 13 y 15 a 19. ¿Te va mejor por la mañana?"*
- **Error interno**: *"Tuve un problema. Intenta de nuevo o usa la reserva manual."*

### RF-CHAT-05: Autenticación en Chat
- **Usuario logueado**: `cliente_id` desde JWT en header/cookie
- **Usuario anónimo**: Permitir consulta disponibilidad, para reservar → pide login
- **Flujo login en chat**: Link a `/login` o modal, tras login retoma contexto

## Tools / Functions para LLM (LangChain)

```python
# Tool 1: Buscar profesionales
@tool
def buscar_profesionales(nombre: str = None, servicio: str = None) -> List[dict]:
    """Busca profesionales por nombre y/o servicio. Retorna: id, nombre, foto, servicios, grilla_resumida"""

# Tool 2: Consultar disponibilidad
@tool
def consultar_disponibilidad(profesional_id: int, fecha_inicio: str, fecha_fin: str, servicio_id: int = None) -> dict:
    """Retorna slots libres agrupados por fecha: {fecha: [{hora_inicio, hora_fin, servicio_id}]}"""

# Tool 3: Verificar slot específico
@tool
def verificar_slot(profesional_id: int, fecha: str, hora_inicio: str, servicio_id: int) -> dict:
    """Valida si slot está libre. Retorna: {disponible: bool, turno_existente: dict|null}"""

# Tool 4: Crear turno (requiere cliente autenticado)
@tool
def crear_turno(cliente_id: int, profesional_id: int, servicio_id: int, fecha: str, hora_inicio: str) -> dict:
    """Crea turno confirmado. Retorna: {turno_id, profesional, servicio, fecha, hora_inicio, hora_fin}"""

# Tool 5: Obtener mis turnos (cliente autenticado)
@tool
def obtener_mis_turnos(cliente_id: int, estado: str = None) -> List[dict]:
    """Retorna turnos del cliente con filtros opcionales"""

# Tool 6: Cancelar turno (cliente autenticado)
@tool
def cancelar_turno(cliente_id: int, turno_id: int) -> dict:
    """Cancela turno del cliente si es futuro (>2h). Retorna: {exitoso: bool, mensaje}"""
```

## Prompt System (Base)

```markdown
Eres "Agendame", asistente virtual de reservas para peluquerías.

PERSONALIDAD: Amable, profesional, conciso. Español rioplatense neutro.

CAPACIDADES:
1. Consultar disponibilidad de peluqueros
2. Reservar turnos
3. Ver/cancelar tus turnos (si estás logueado)

REGLAS:
- Siempre verifica disponibilidad ANTES de confirmar reserva
- Si falta info, pregunta UNA cosa a la vez
- Usa herramientas (tools) para datos reales, no inventes
- Si error en tool, avisa al usuario y sugiere alternativa
- Máximo 3 mensajes sin resolver → ofrece reserva manual web

FLUJO TÍPICO:
Usuario: "Quiero corte con Juan"
Tú: [buscar_profesionales(nombre="Juan")] → "Juan atiende Lun-Vie 9-13/15-19. ¿Qué día?"
Usuario: "El jueves"
Tú: [consultar_disponibilidad(profesional_id=1, fecha_inicio="2026-10-15", fecha_fin="2026-10-15")] → "Jueves 15: 9:00, 9:30, 10:00, 15:00, 15:30. ¿Horario?"
Usuario: "10:00"
Tú: [verificar_slot(...)] → [crear_turno(...)] → "¡Confirmado! Corte con Juan el jueves 15 a las 10:00."
```

## Integración Backend-Frontend

### Endpoint Chat
```python
POST /chat/message
Headers: Authorization: Bearer <jwt> (opcional)
Body: { "mensaje": "string", "session_id": "uuid" }
Response: { "respuesta": "string", "session_id": "uuid", "acciones": [...] }
```

### WebSocket (Opcional - Tiempo Real)
```python
WS /chat/ws/{session_id}
# Mensajes bidireccionales, typing indicators, streaming de respuesta LLM
```

### Contexto de Sesión (Redis / Memoria)
```python
ChatSession:
  - session_id: UUID
  - cliente_id: int | None
  - mensajes: List[ChatMessage]  # últimos 10
  - entidades_actuales: {
      profesional_id: int | None,
      servicio_id: int | None,
      fecha_referencia: date | None
    }
  - creado_en: datetime
  - actualizado_en: datetime
```

## Configuración Groq / LangChain

```python
# LLM Config
model = "openai/gpt-oss-120b"  # o "openai/gpt-oss-20b" / "qwen/qwen3.8-27b"
temperature = 0.1  # determinista para tool calling
max_tokens = 1024

# LangChain Agent
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)
```

## Variables de Entorno

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
CHAT_MODEL=openai/gpt-oss-120b
CHAT_TEMPERATURE=0.1
CHAT_MAX_HISTORY=10
CHAT_SESSION_TTL=3600  # segundos
```

## Criterios de Aceptación

1. Usuario pregunta *"Horarios de Juan mañana"* → responde con slots reales
2. Usuario dice *"Reservo corte con Juan mañana a las 10"* → crea turno real
3. Usuario no logueado intenta reservar → pide login, retoma tras autenticar
4. Slot no disponible → informa alternativas reales
5. Profesional inexistente → sugiere profesionales reales disponibles
6. Conversación mantiene contexto (profesional, servicio, fecha) entre mensajes
7. Respuesta < 3 segundos (Groq fast inference)
8. Logs de conversación para auditoría (sin PII sensible)

## Requirements

<!-- Agregados por el change cu-05-06-chatbot (CU-05/06) -->

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
