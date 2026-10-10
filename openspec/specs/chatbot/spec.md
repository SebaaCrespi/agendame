# Especificación de Dominio: Chatbot / Asistente Virtual (CU-05, CU-06)

## Resumen

Asistente conversacional integrado (LangChain + Groq API) para consulta de disponibilidad y agendamiento de turnos por lenguaje natural. Expone herramientas (tools/functions) que el LLM invoca para interactuar con el backend.

## Arquitectura

```
Usuario (Frontend Chat) 
    ↓ WebSocket / REST
Backend FastAPI (Chatbot Service)
    ↓ LangChain Agent (ReAct / OpenAI Functions)
Groq API (LLM: llama-3.3-70b-versatile / mixtral-8x7b)
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
model = "llama-3.3-70b-versatile"  # o "mixtral-8x7b-32768"
temperature = 0.1  # determinista para tool calling
max_tokens = 1024

# LangChain Agent
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)
```

## Variables de Entorno

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
CHAT_MODEL=llama-3.3-70b-versatile
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