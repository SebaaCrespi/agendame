# Tasks: CU-05 y CU-06 Asistente virtual de turnos

## 1. Dependencias y configuración

- [x] 1.1 Corregir la línea pegada de `requirements.txt` y agregar `langchain-core`, `langchain-groq`, `langchain-nvidia-ai-endpoints` y `langchain-ollama`; agregar a `config.py` `CHAT_PROVIDER`, `NVIDIA_API_KEY`, `OLLAMA_BASE_URL`, `CHAT_TEMPERATURE`, `CHAT_TIMEOUT_S`, `CHAT_MAX_HISTORY` y `CHAT_SESSION_TTL`, y documentarlas en `AGENTS.md`. Verificar: `pip install -r requirements.txt` y la suite actual en verde
- [x] 1.2 Crear `services/chat_llm.py` (`crear_llm` por proveedor con imports perezosos) y el `FakeToolModel` de tests. Verificar: test de que cada proveedor arma la clase correcta y de que un proveedor desconocido falla con mensaje claro

## 2. Herramientas y servicio

- [x] 2.1 Crear `services/chat_tools.py` con las cinco herramientas ligadas al `cliente_id` de la sesión y errores de dominio devueltos como texto. Verificar: tests de cada herramienta contra la DB de tests (incluye sin sesión, horario ocupado, cancelación a menos de 2 h y que `reservar_turno` usa el cliente de la sesión)
- [x] 2.2 Crear `ChatSessionStore` y `ChatbotService.responder` (system prompt con fecha del negocio, bucle de hasta 5 vueltas, historial de 10, `acciones`). Verificar: tests con `FakeToolModel` para respuesta directa, una herramienta, dos herramientas encadenadas, límite de vueltas, historial recortado, conversación ajena y vencimiento

## 3. Endpoint

- [x] 3.1 Crear `schemas/chat.py` y `POST /api/v1/chat/message` (auth opcional, límite 20/min, 503 ante fallos del proveedor). Verificar: tests de API para cliente con sesión, sin sesión, mensaje vacío (422), proveedor caído (503) y 429

## 4. Interfaz

- [x] 4.1 Crear `components/chat/ChatWidget.tsx`, `api.enviarMensajeChat` y tipos; montarlo en el panel del cliente y refrescar "Mis turnos" con `acciones`. Verificar: `npm run build` y `npm run lint` sin errores

## 5. Comparación de modelos

- [x] 5.1 Crear `scripts/comparar_modelos.py` (4 conversaciones guionadas, proveedores con key, copia temporal de la DB, tabla de resultados). Verificar: corre sin keys mostrando qué proveedores se saltearon; con keys, imprime la tabla

## 6. Verificación end-to-end

- [ ] 6.1 Con una key real de Groq: en el navegador, como cliente, consultar horarios de Juan para mañana, reservar con confirmación, ver el turno en "Mis turnos", pedir cancelarlo y confirmar; preguntar por un profesional inexistente. Revisar el chat a 375 px. Verificar: capturas
- [x] 6.2 Suite completa en verde y `ruff check app/` limpio. Verificar: `pytest` y `ruff check app/`

## Workflow follow-up

- Correr `scripts/comparar_modelos.py` con las keys de Groq y NVIDIA y elegir el modelo por defecto
- `/opsx-archive` del change una vez implementado y revisado
- `mem_save` en Engram con las decisiones (herramientas ligadas a la sesión, bucle propio, proveedor por `.env`)
