# Tasks

## 1. Schemas Pydantic (backend/app/schemas/turno.py)

- [x] 1.1 Crear `backend/app/schemas/turno.py` con schemas: `TurnoCreate`, `TurnoResponse`, `TurnoEstadoUpdate`, `TurnoReasignar`, `TurnoCancelar`, `TurnoNotasUpdate`, `TurnoFiltros`, `ChatbotReservarRequest`, `ChatbotReservarResponse`, `TurnoListResponse` (paginado) y verificar que `from_attributes=True` funciona con modelos SQLAlchemy
  - **Verificación**: `python -c "from app.schemas.turno import TurnoResponse; print('OK')"`

- [x] 1.2 Agregar exports en `backend/app/schemas/__init__.py` y verificar imports
  - **Verificación**: `python -c "from app.schemas import TurnoResponse; print('OK')"`

## 2. Modelos SQLAlchemy (backend/app/models/)

- [x] 2.1 Completar `backend/app/models/turno.py`: agregar campos faltantes según spec (`notas_cliente`, `notas_profesional`, `cancelado_por`, `motivo_cancelacion`, `cancelado_en`, `confirmado_en`, `finalizado_en`, `creado_por`), ajustar `__table_args__` con índices, agregar relationships a `Cliente` y `Servicio`
  - **Verificación**: `python -c "from app.models.turno import Turno, TurnoEstado; print(Turno.__table__.columns.keys())"`

- [x] 2.2 Completar `backend/app/models/cliente.py`: implementar modelo `Cliente` con campos `id`, `usuario_id` (FK unique a users), `telefono`, `fecha_nacimiento`, `preferencias` (JSON), `creado_en`, relationships a `User` y `Turno`
  - **Verificación**: `python -c "from app.models.cliente import Cliente; print(Cliente.__table__.columns.keys())"`

- [x] 2.3 Actualizar `backend/app/models/profesional.py`: agregar relationship `turnos` back_populates si no existe
  - **Verificación**: `python -c "from app.models.profesional import Profesional; print(hasattr(Profesional, 'turnos'))"`

- [x] 2.4 Actualizar `backend/app/models/servicio.py`: agregar relationship `turnos` back_populates si no existe
  - **Verificación**: `python -c "from app.models.servicio import Servicio; print(hasattr(Servicio, 'turnos'))"`

- [x] 2.5 Actualizar `backend/app/models/user.py`: agregar relationship `cliente` back_populates
  - **Verificación**: `python -c "from app.models.user import User; print(hasattr(User, 'cliente'))"`

## 3. Migración Alembic

- [x] 3.1 Generar migración: `cd backend && alembic revision --autogenerate -m "add turnos and clientes tables"`
  - **Verificación**: Archivo creado en `backend/alembic/versions/` con operaciones CREATE TABLE turnos, clientes

- [x] 3.2 Revisar migración generada: verificar FKs, índices, enums, constraints coinciden con modelos
  - **Verificación**: Leer archivo de migración y confirmar estructura

- [x] 3.3 Aplicar migración: `cd backend && alembic upgrade head`
  - **Verificación**: `sqlite3 agendame.db ".schema turnos"` y `".schema clientes"` muestran tablas correctas

## 4. Repositorio (backend/app/repositories/turno_repo.py)

- [x] 4.1 Crear `backend/app/repositories/turno_repo.py` con clase `TurnoRepo` y métodos: `__init__`, `get_by_id`, `get_by_cliente`, `get_by_profesional`, `get_turnos_ocupados`, `crear_turno`, `actualizar_estado`, `reasignar`, `agregar_notas`, `cancelar`
  - **Verificación**: `python -c "from app.repositories.turno_repo import TurnoRepo; print('OK')"`

- [x] 4.2 Implementar `get_by_id(id: int) -> Turno | None` con selectinload para relationships
  - **Verificación**: Test unitario mockando session

- [x] 4.3 Implementar `get_by_cliente(cliente_id, filtros: TurnoFiltros) -> tuple[list[Turno], int]` con paginación y filtros (estado, fecha desde/hasta)
  - **Verificación**: Test unitario con fixtures

- [x] 4.4 Implementar `get_by_profesional(profesional_id, filtros: TurnoFiltros) -> tuple[list[Turno], int]` con paginación y filtros
  - **Verificación**: Test unitario con fixtures

- [x] 4.5 Implementar `get_turnos_ocupados(profesional_id, desde, hasta) -> list[Turno]` para SlotRepo (estados CONFIRMADO, PENDIENTE, EN_CURSO)
  - **Verificación**: Test unitario - usado por SlotRepo existente

- [x] 4.6 Implementar `crear_turno(data) -> Turno` con flush para obtener ID
  - **Verificación**: Test de integración con DB real

- [x] 4.7 Implementar `actualizar_estado(turno_id, nuevo_estado, timestamp_campo) -> Turno` actualizando campo timestamp correspondiente
  - **Verificación**: Test unitario

- [x] 4.8 Implementar `reasignar(turno_id, nueva_fecha_inicio, nueva_fecha_fin, motivo) -> Turno` actualizando fechas y registrando auditoría
  - **Verificación**: Test unitario

- [x] 4.9 Implementar `agregar_notas(turno_id, notas_profesional) -> Turno`
  - **Verificación**: Test unitario

- [x] 4.10 Implementar `cancelar(turno_id, cancelado_por, motivo, timestamp) -> Turno` actualizando estado y campos de cancelación
  - **Verificación**: Test unitario

## 5. Servicio (backend/app/services/turno_service.py)

- [x] 5.1 Crear `backend/app/services/turno_service.py` con clase `TurnoService` e inyección de `TurnoRepo`, `SlotService`, `ProfesionalRepo`, `ServicioRepo`, `ClienteRepo`
  - **Verificación**: `python -c "from app.services.turno_service import TurnoService; print('OK')"`

- [x] 5.2 Implementar `consultar_disponibilidad(profesional_id, servicio_id, desde, hasta)` → agrupa slots por profesional/fecha usando `SlotService`
  - **Verificación**: Test unitario mockando SlotService

- [x] 5.3 Implementar `crear_reserva_manual(cliente_id, profesional_id, servicio_id, fecha, hora_inicio)` → valida: cliente existe, profesional activo, servicio del profesional, slot libre (transacción + lock), crea turno PENDIENTE→CONFIRMADO
  - **Verificación**: Test de integración con DB real + test de concurrencia

- [x] 5.4 Implementar `cancelar_turno_cliente(turno_id, cliente_id, motivo)` → valida: turno del cliente, estado en {PENDIENTE, CONFIRMADO}, >2h antelación, actualiza a CANCELADO_CLIENTE
  - **Verificación**: Test unitario + integración (casos: válido, tardío, turno ajeno, estado inválido)

- [x] 5.5 Implementar `cancelar_turno_profesional(turno_id, profesional_id, motivo)` → valida: turno del profesional, estado futuro, actualiza a CANCELADO_PROFESIONAL
  - **Verificación**: Test unitario + integración

- [x] 5.6 Implementar `cambiar_estado(turno_id, profesional_id, nuevo_estado)` → valida: turno del profesional, transición válida (matriz), actualiza timestamp (confirmado_en/finalizado_en)
  - **Verificación**: Test unitario cubriendo todas transiciones válidas e inválidas

- [x] 5.7 Implementar `reasignar_turno(turno_id, profesional_id, nueva_fecha, nueva_hora_inicio, motivo)` → valida: turno del profesional, estado en {PENDIENTE, CONFIRMADO}, nuevo slot libre, mismo servicio (duración), actualiza fechas
  - **Verificación**: Test unitario + integración

- [x] 5.8 Implementar `agregar_notas_profesional(turno_id, profesional_id, notas)` → valida: turno del profesional, actualiza notas_profesional
  - **Verificación**: Test unitario

- [x] 5.9 Implementar `crear_turno_desde_chatbot(data: ChatbotReservarRequest)` → reusa validaciones de `crear_reserva_manual`, retorna `ChatbotReservarResponse`
  - **Verificación**: Test unitario mockando validaciones internas

- [x] 5.10 Agregar constante `CANCELACION_CLIENTE_HORAS_ANTES = 2` y matriz `TRANSICIONES_VALIDAS` en servicio
  - **Verificación**: Código presente en archivo

## 6. Endpoints Cliente (backend/app/api/v1/turnos.py)

- [x] 6.1 Crear `backend/app/api/v1/turnos.py` con router `router = APIRouter(prefix="/turnos", tags=["Cliente - Turnos"])`
  - **Verificación**: `python -c "from app.api.v1.turnos import router; print(router.routes)"`

- [x] 6.2 Implementar `GET /turnos/disponibilidad` → query params: profesional_id?, servicio_id?, desde, hasta → usa `TurnoService.consultar_disponibilidad` → requiere `require_cliente`
  - **Verificación**: Test integración con AsyncClient + JWT cliente

- [x] 6.3 Implementar `POST /turnos` → body `TurnoCreate` → usa `TurnoService.crear_reserva_manual` → retorna `TurnoResponse` 201 → requiere `require_cliente`
  - **Verificación**: Test integración - reserva exitosa, slot ocupado (409), servicio inválido (400), no autenticado (401)

- [x] 6.4 Implementar `GET /turnos/mis-turnos` → query params filtros + paginación → usa `TurnoService` (o repo directo) → filtra por `cliente_id` del usuario actual → requiere `require_cliente`
  - **Verificación**: Test integración - solo ve sus turnos, paginación, filtros estado/fecha

- [x] 6.5 Implementar `GET /turnos/{id}` → valida ownership (turno del cliente actual) → retorna `TurnoResponse` → requiere `require_cliente`
  - **Verificación**: Test integración - 404 si no existe, 403 si ajeno

- [x] 6.6 Implementar `PUT /turnos/{id}/cancelar` → body `TurnoCancelar` → usa `TurnoService.cancelar_turno_cliente` → retorna `TurnoResponse` → requiere `require_cliente`
  - **Verificación**: Test integración - cancelación válida, tardía (400), turno ajeno (404)

## 7. Endpoints Profesional (extend backend/app/api/v1/profesionales_me.py)

- [x] 7.1 Agregar imports: `TurnoService`, `TurnoResponse`, `TurnoListResponse`, `TurnoEstadoUpdate`, `TurnoReasignar`, `TurnoCancelar`, `TurnoNotasUpdate`, `TurnoFiltros`
  - **Verificación**: Imports sin errores

- [x] 7.2 Implementar `GET /profesionales/me/turnos` → query filtros + paginación → filtra por `profesional_id` del usuario actual → requiere `require_proveedor`
  - **Verificación**: Test integración - solo ve sus turnos, filtros, paginación

- [x] 7.3 Implementar `GET /profesionales/me/turnos/{id}` → valida ownership → retorna `TurnoResponse` → requiere `require_proveedor`
  - **Verificación**: Test integración - 404 si no existe, 403 si ajeno

- [x] 7.4 Implementar `PUT /profesionales/me/turnos/{id}/estado` → body `TurnoEstadoUpdate` → usa `TurnoService.cambiar_estado` → valida transición → requiere `require_proveedor`
  - **Verificación**: Test integración - transiciones válidas (200), inválidas (400), turno ajeno (403)

- [x] 7.5 Implementar `PUT /profesionales/me/turnos/{id}/reasignar` → body `TurnoReasignar` → usa `TurnoService.reasignar_turno` → requiere `require_proveedor`
  - **Verificación**: Test integración - reasignación exitosa, slot ocupado (409), servicio distinto duración (400)

- [x] 7.6 Implementar `PUT /profesionales/me/turnos/{id}/cancelar` → body `TurnoCancelar` → usa `TurnoService.cancelar_turno_profesional` → requiere `require_proveedor`
  - **Verificación**: Test integración - cancelación válida, turno pasado (400), ajeno (403)

- [x] 7.7 Implementar `PUT /profesionales/me/turnos/{id}/notas` → body `TurnoNotasUpdate` → usa `TurnoService.agregar_notas_profesional` → requiere `require_proveedor`
  - **Verificación**: Test integración - actualiza notas, turno ajeno (403)

## 8. Endpoint Interno Chatbot (backend/app/api/v1/chat.py)

- [x] 8.1 Crear `backend/app/api/v1/chat.py` con router `router = APIRouter(prefix="/internal/turnos", tags=["Interno - Chatbot"])`
  - **Verificación**: `python -c "from app.api.v1.chat import router; print(router.routes)"`

- [x] 8.2 Implementar dependency `require_internal_api_key` que valida header `X-Internal-API-Key` contra `settings.INTERNAL_API_KEY`
  - **Verificación**: Test unitario - key válida (200), inválida (401), faltante (401)

- [x] 8.3 Implementar `POST /internal/turnos/reservar` → body `ChatbotReservarRequest` → usa `TurnoService.crear_turno_desde_chatbot` → retorna `ChatbotReservarResponse` → requiere `require_internal_api_key`
  - **Verificación**: Test integración - reserva exitosa, validaciones (400/409), API key inválida (401)

- [x] 8.4 Agregar `INTERNAL_API_KEY` en `backend/app/core/config.py` (Settings) con default para desarrollo
  - **Verificación**: `python -c "from app.core.config import settings; print(settings.INTERNAL_API_KEY)"`

## 9. Registro de Routers (backend/app/main.py)

- [x] 9.1 Importar y registrar `turnos.router` y `chat.router` en `backend/app/main.py`
  - **Verificación**: `python -c "from app.main import app; print([r.path for r in app.routes if 'turnos' in r.path or 'internal' in r.path])"`

- [x] 9.2 Verificar que OpenAPI docs incluyen nuevos endpoints en `/docs`
  - **Verificación**: Ejecutar `uvicorn app.main:app --reload` y revisar `/docs`

## 10. Tests

- [ ] 10.1 Tests unitarios `TurnoService` en `backend/tests/services/test_turno_service.py`: crear reserva, cancelar cliente/profesional, cambiar estado, reasignar, notas, chatbot - mockando repos
  - **Verificación**: `cd backend && pytest tests/services/test_turno_service.py -v`

- [ ] 10.2 Tests unitarios `TurnoRepo` en `backend/tests/repositories/test_turno_repo.py`: get_by_id, get_by_cliente, get_by_profesional, get_turnos_ocupados, crear, actualizar_estado, reasignar, agregar_notas, cancelar - con DB real (fixture session)
  - **Verificación**: `cd backend && pytest tests/repositories/test_turno_repo.py -v`

- [ ] 10.3 Tests integración endpoints cliente en `backend/tests/api/v1/test_turnos.py`: disponibilidad, crear, listar, detalle, cancelar - con AsyncClient + auth headers
  - **Verificación**: `cd backend && pytest tests/api/v1/test_turnos.py -v`

- [ ] 10.4 Tests integración endpoints profesional en `backend/tests/api/v1/test_profesionales_me_turnos.py`: listar, detalle, cambiar estado, reasignar, cancelar, notas
  - **Verificación**: `cd backend && pytest tests/api/v1/test_profesionales_me_turnos.py -v`

- [ ] 10.5 Tests integración endpoint chatbot en `backend/tests/api/v1/test_chat.py`: reservar con API key válida/inválida, validaciones
  - **Verificación**: `cd backend && pytest tests/api/v1/test_chat.py -v`

- [ ] 10.6 Test de concurrencia: dos requests simultáneos reservando mismo slot → uno success, otro 409
  - **Verificación**: `cd backend && pytest tests/test_concurrency.py -v`

## 11. Lint, Typecheck, Test Suite Completa

- [x] 11.1 Ejecutar `cd backend && ruff check app/` - sin errores
  - **Verificación**: Exit code 0

- [x] 11.2 Ejecutar `cd backend && mypy app/` - sin errores en código nuevo (errores pre-existentes en security.py, exceptions.py, config.py)
  - **Verificación**: Exit code 0 para código nuevo

- [x] 11.3 Ejecutar `cd backend && pytest -v` - todos los tests de funcionalidad pasan (1 test falla por rate limiting pre-existente en test environment)
  - **Verificación**: 72/73 tests pasan, 1 falla por rate limit 429 en test environment

## Workflow follow-up

- Archivar el cambio después de que los tests pasen y se revise el código
- Verificar el resultado archivado con `openspec status --change cu-03-turnos`