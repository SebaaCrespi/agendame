# Design: CU-05 y CU-06 Asistente virtual de turnos

## Context

El motivo está en proposal.md y el comportamiento en `specs/chatbot`. Estado actual:

- `api/v1/chat.py` solo tiene `POST /internal/turnos/reservar` (con `X-Internal-API-Key`), que llama a `TurnoService.crear_turno_desde_chatbot`.
- Los servicios ya resuelven todo lo que el asistente necesita: `ProfesionalService` (listado público), `TurnoService.consultar_disponibilidad`, `crear_reserva_manual`, `get_turnos_by_cliente` (con `momento`, CU-09) y `cancelar_turno_cliente`.
- `config.py` tiene `GROQ_API_KEY` y `CHAT_MODEL`; no hay LangChain instalado. En LangChain 1.x, `AgentExecutor` quedó como legado.
- `slowapi` ya está configurado (`limiter` en `api/deps.py`).
- El spec de dominio original pasaba `cliente_id` como argumento de las herramientas; se reemplaza por la identidad de la sesión.

## Goals / Non-Goals

**Goals:**
- Que el modelo solo pueda actuar a través de herramientas que reutilizan los servicios y sus validaciones.
- Cambiar de proveedor sin tocar código, y testear todo sin red.

**Non-Goals:**
- Persistencia de conversaciones, streaming o WebSocket.
- Un framework de agentes con planificación propia.

## Decisions

### 1. Bucle de herramientas propio sobre `bind_tools`
`ChatbotService.responder(session, mensaje)` arma los mensajes (system prompt + historial + mensaje nuevo), llama a `llm.bind_tools(tools).ainvoke(...)` y, mientras la respuesta traiga `tool_calls`, ejecuta cada herramienta, agrega un `ToolMessage` con el resultado y vuelve a llamar. Máximo 5 vueltas; si se agotan, responde que no pudo resolverlo y sugiere la reserva manual.
- *Alternativa*: `create_agent` / `AgentExecutor`. Se descarta para el TP: el bucle propio tiene 30 líneas, es fácil de testear con un modelo falso y no depende de cómo cada versión de LangChain arma el agente.

### 2. Herramientas ligadas a la sesión
`chat_tools.crear_herramientas(session_db, cliente_id | None)` devuelve funciones `@tool` con el `cliente_id` capturado por cierre: el modelo no recibe ni puede pasar ese dato.
- `buscar_profesionales(nombre?: str)` → id, nombre y servicios (id, nombre, duración, precio) de los activos.
- `consultar_disponibilidad(profesional_id, servicio_id, desde, hasta)` → horarios libres por fecha; rango máximo 14 días.
- `reservar_turno(profesional_id, servicio_id, fecha, hora)` → `crear_reserva_manual` con el cliente de la sesión.
- `mis_turnos()` → próximos turnos del cliente (`momento=proximos`).
- `cancelar_turno(turno_id, motivo)` → `cancelar_turno_cliente` con el cliente de la sesión.

Sin cliente, las tres últimas devuelven "Necesitás iniciar sesión como cliente". Las excepciones de dominio (`ValidationException`, `ConflictException`, `NotFoundException`) se devuelven al modelo como texto ("Error: el horario ya no está disponible") para que explique y ofrezca alternativas; cualquier otra excepción se registra y corta la respuesta con el mensaje de error interno.

La confirmación antes de reservar o cancelar es una regla del system prompt, no un paso técnico. Se acepta: la herramienta valida todo lo demás y el modelo de 70B la respeta; los tests de servicio verifican que el bucle no reserva si el modelo falso no lo pide.

### 3. Proveedor por configuración
`chat_llm.crear_llm(settings)` devuelve un `BaseChatModel` según `CHAT_PROVIDER`:
- `groq` → `ChatGroq(model=CHAT_MODEL, api_key=GROQ_API_KEY)`
- `nvidia` → `ChatNVIDIA(model=CHAT_MODEL, api_key=NVIDIA_API_KEY)`
- `ollama` → `ChatOllama(model=CHAT_MODEL, base_url=OLLAMA_BASE_URL)`

Con `temperature=CHAT_TEMPERATURE` (0.1) y `timeout=CHAT_TIMEOUT_S` (20). Los imports son perezosos: solo se importa el paquete del proveedor elegido. `ChatbotService` recibe el modelo por inyección (dependencia de FastAPI), y los tests lo reemplazan por `FakeToolModel`, un modelo falso que devuelve una lista de respuestas guionadas y registra lo que recibió.

### 4. Sesiones en memoria
`ChatSessionStore`: diccionario `session_id → (user_id | None, mensajes, actualizado_en)`, con lock asíncrono. Se guardan solo mensajes de usuario y respuestas finales del asistente (no los resultados de herramientas), recortados a los últimos 10. Se purgan las vencidas (1 h) en cada acceso. Si el `session_id` no existe o pertenece a otro usuario, se crea uno nuevo y se devuelve en la respuesta. Vale para un único proceso, como el lock de reservas.

### 5. Endpoint
`POST /api/v1/chat/message` con `ChatMessageRequest {mensaje: 1–1000 caracteres, session_id?: str}` y `ChatMessageResponse {respuesta, session_id, acciones: list[str]}`. `acciones` lista lo que cambió (`"turno_reservado"`, `"turno_cancelado"`) para que el frontend refresque. Autenticación opcional (`get_current_user_optional`); solo el rol CLIENTE habilita las herramientas de cliente. `@limiter.limit("20/minute")`. Errores del proveedor (timeout, conexión, 5xx, falta de key) → 503 con `detail` "El asistente no está disponible ahora. Podés reservar desde «Reservar turno»."

### 6. System prompt
Plantilla en español con: fecha y día de hoy según `ahora_negocio()`, reglas (usar herramientas, no inventar, preguntar de a una cosa, confirmar antes de reservar o cancelar, responder breve), y formato de horas HH:MM. Se arma en cada mensaje para que la fecha esté al día.

### 7. Frontend
`ChatWidget`: botón flotante abajo a la derecha en `ClienteDashboard`; panel con la conversación, input, estado "escribiendo…" y errores. Guarda `session_id` en `sessionStorage` (envuelto en try/catch). Cuando la respuesta trae `acciones`, llama a un callback que recarga `MisTurnosCliente`. A 375 px el panel ocupa el ancho con 16 px de margen.

### 8. Comparación de modelos
`scripts/comparar_modelos.py`: corre 4 conversaciones guionadas (consulta simple, profesional inexistente, reserva con confirmación, cancelación) contra cada combinación proveedor/modelo de una lista, solo si hay key para ese proveedor, sobre una copia temporal de la DB de desarrollo. Reporta por caso: herramientas llamadas, si fueron las esperadas, y latencia. No se ejecuta en `pytest`.

## Risks / Trade-offs

- [El modelo reserva sin confirmar] → Regla en el prompt, temperatura baja; la reserva igual pasa todas las validaciones y queda a nombre del cliente correcto. Se mide en la comparación de modelos.
- [Sesiones en memoria] → Se pierden al reiniciar y no escalan a varios procesos; aceptable para el TP.
- [Cupo del plan gratuito] → 503 con mensaje claro; el proveedor se cambia por `.env`.
- [Datos personales al proveedor] → Las herramientas devuelven nombres de profesionales y servicios, y los turnos del propio cliente; nunca datos de otros clientes. Los logs registran nombres de herramientas e ids, no el texto de los mensajes.

## Migration Plan

Sin migraciones de base. Instalar dependencias (`pip install -r requirements.txt`) y cargar las keys en `backend/.env`. Sin key válida, el resto de la app funciona igual y el chat responde 503.
