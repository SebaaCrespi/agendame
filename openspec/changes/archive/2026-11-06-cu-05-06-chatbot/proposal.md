# Proposal: CU-05 y CU-06 Asistente virtual de turnos

## Why

CU-05 y CU-06 piden que el cliente consulte disponibilidad y reserve un turno escribiendo en lenguaje natural. Hoy no hay asistente: no está el servicio, ni `POST /chat/message`, ni la interfaz de chat, ni las dependencias de LangChain. Solo existe el endpoint interno de reserva (`/internal/turnos/reservar`). Además, `requirements.txt` tiene dos paquetes pegados en una línea y `pip install -r` falla.

## What Changes

- **Asistente con herramientas**: un servicio que conversa con un modelo de lenguaje (LangChain) y le da cinco herramientas: buscar profesionales, consultar disponibilidad, reservar, ver mis próximos turnos y cancelar. Cada herramienta usa los servicios existentes con sus validaciones; el modelo nunca accede directo a la base.
- **Proveedor configurable**: `CHAT_PROVIDER` (`groq` por defecto, `nvidia` u `ollama`) y `CHAT_MODEL` en el `.env`, con la key de cada proveedor. Si el proveedor falla, el chat responde que use la reserva manual.
- **Identidad desde la sesión**: el cliente de las reservas y cancelaciones sale del JWT, nunca de lo que diga el modelo. Sin sesión de cliente, el asistente consulta pero no reserva.
- **`POST /api/v1/chat/message`**: recibe el mensaje y un `session_id`; guarda en memoria los últimos 10 mensajes de cada conversación (vence tras 1 h sin uso); límite de 20 mensajes por minuto.
- **Reglas del asistente**: usa la fecha de hoy (hora del negocio) para "mañana" o "el viernes", no inventa horarios, y pide confirmación antes de reservar o cancelar.
- **Interfaz**: un botón de chat flotante en el panel del cliente; al reservar o cancelar, "Mis turnos" se actualiza.
- **Comparación de modelos**: un script que corre conversaciones de prueba contra los proveedores con key configurada (Groq y modelos de NVIDIA) y muestra si eligieron la herramienta correcta y cuánto tardaron.
- Se corrige `requirements.txt` y se agregan las dependencias de LangChain.

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `chatbot`: se definen las herramientas, la identidad desde la sesión, el contexto de conversación, la confirmación antes de reservar, los errores, el proveedor configurable y la interfaz.

## Impact

- **Backend**: nuevos `services/chatbot_service.py`, `services/chat_tools.py`, `services/chat_llm.py`, `schemas/chat.py`; `api/v1/chat.py` (endpoint nuevo); `core/config.py`; `requirements.txt`; `scripts/comparar_modelos.py`; tests con un modelo falso (sin red).
- **Frontend**: nuevo `components/chat/ChatWidget.tsx`; `services/api.ts`, `types/index.ts` y el panel del cliente.
- **Configuración**: el usuario carga en `backend/.env` sus keys reales (`GROQ_API_KEY`, `NVIDIA_API_KEY`); la de ejemplo actual no sirve.

## Fuera de alcance

- WebSocket o respuestas en streaming.
- Guardar conversaciones en la base o en Redis (se pierden al reiniciar el servidor).
- Chat para visitantes sin sesión en la interfaz (la API lo admite solo para consultar).
- Reasignar turnos o cambiar de servicio desde el chat.
- Modelos gratuitos de OpenCode Zen.
