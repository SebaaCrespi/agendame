# Tasks

## 1. Setup y Modelos

- [x] 1.1 Crear `backend/app/models/profesional.py` con `Profesional`, `Servicio`, `Disponibilidad`, `ExcepcionDisponibilidad`; verificar `python -c "from app.models.profesional import Profesional, Servicio; print(Profesional.__tablename__)"`
- [x] 1.2 Actualizar `backend/app/models/__init__.py` exportando nuevos modelos; verificar imports
- [x] 1.3 Generar migración: `cd backend && alembic revision --autogenerate -m "profesionales_servicios_disponibilidad"`; verificar archivo en `alembic/versions/`
- [x] 1.4 Aplicar migración: `cd backend && alembic upgrade head`; verificar `sqlite3 agendame.db ".schema profesionales"`

## 2. Schemas Pydantic (Request/Response)

- [x] 2.1 Crear `backend/app/schemas/profesional.py`: `ProfesionalCreate`, `ProfesionalUpdate`, `ProfesionalResponse`, `ProfesionalListResponse`, `ServicioCreate`, `ServicioUpdate`, `ServicioResponse`, `DisponibilidadCreate`, `DisponibilidadUpdate`, `DisponibilidadResponse`, `ExcepcionCreate`, `ExcepcionResponse`, `SlotResponse`, `SlotsListResponse`; verificar validaciones (unicidad nombre servicio, duracion > 0, precio >= 0)
- [x] 2.2 Crear `backend/app/schemas/pagination.py`: `PageParams`, `PageResponse`, `FilterParams` genéricos; verificar con test
- [x] 2.3 Actualizar `backend/app/schemas/__init__.py` exportando nuevos schemas

## 3. Repositorios (Data Access)

- [x] 3.1 Implementar `backend/app/repositories/profesional_repo.py`: `ProfesionalRepo` con `create`, `get_by_id`, `get_by_user_id`, `get_by_email`, `list_paginated`, `update`, `soft_delete`, `get_by_id_with_relations`
- [x] 3.2 Implementar `backend/app/repositories/servicio_repo.py`: `ServicioRepo` con `create`, `get_by_id`, `get_by_profesional`, `get_by_id_and_profesional`, `list_by_profesional`, `update`, `soft_delete`, `exists_nombre_for_profesional`
- [x] 3.3 Implementar `backend/app/repositories/disponibilidad_repo.py`: `DisponibilidadRepo` con `create`, `get_by_id`, `get_by_profesional`, `replace_all_for_profesional` (bulk replace grilla semanal), `delete_by_profesional`
- [x] 3.4 Implementar `backend/app/repositories/excepcion_repo.py`: `ExcepcionRepo` con `create`, `get_by_id`, `get_by_profesional`, `get_by_profesional_and_fecha`, `list_by_profesional`, `delete`, `delete_by_profesional`
- [x] 3.5 Implementar `backend/app/repositories/slot_repo.py`: `SlotRepo` con `get_slots_disponibles(profesional_id, desde, hasta)` - lógica core de generación de slots
- [x] 3.6 Actualizar `backend/app/repositories/__init__.py` exportando nuevos repos

## 4. Servicios (Business Logic)

- [x] 4.1 Implementar `backend/app/services/profesional_service.py`: `ProfesionalService` con `crear_profesional_admin`, `obtener_profesional`, `listar_profesionales_admin`, `actualizar_profesional`, `desactivar_profesional` (validar turnos futuros), `obtener_mi_perfil`, `actualizar_mi_perfil`
- [x] 4.2 Implementar `backend/app/services/servicio_service.py`: `ServicioService` con `crear_servicio`, `obtener_servicio`, `listar_mis_servicios`, `actualizar_servicio`, `desactivar_servicio`; validar unicidad nombre por profesional
- [x] 4.3 Implementar `backend/app/services/disponibilidad_service.py`: `DisponibilidadService` con `obtener_mi_grilla`, `actualizar_grilla_completa` (bulk replace), `obtener_excepciones`, `agregar_excepcion`, `eliminar_excepcion`
- [x] 4.4 Implementar `backend/app/services/slot_service.py`: `SlotService` con `generar_slots_disponibles(profesional_id, desde, hasta)` - algoritmo core: expandir grilla + aplicar excepciones + generar slots base + filtrar turnos ocupados
- [x] 4.5 Tests unitarios services con mock repo (≥85% coverage): `pytest tests/services/test_profesional_service.py -v`, `pytest tests/services/test_slot_service.py -v`

## 5. Endpoints API (Controllers)

- [x] 5.1 Implementar `backend/app/api/v1/profesionales_admin.py`: router `/admin/profesionales` (ADMIN) - `POST`, `GET /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}` (soft delete con validación turnos futuros)
- [x] 5.2 Implementar `backend/app/api/v1/profesionales_me.py`: router `/profesionales/me` (PROVEEDOR) - `GET /`, `PUT /`, `GET /servicios`, `POST /servicios`, `PUT /servicios/{id}`, `DELETE /servicios/{id}`, `GET /disponibilidad`, `PUT /disponibilidad`, `POST /excepciones`, `DELETE /excepciones/{id}`
- [x] 5.3 Implementar `backend/app/api/v1/profesionales_public.py`: router `/profesionales` (Público/CLIENTE) - `GET /` (paginado, filtros), `GET /{id}` (perfil + servicios + grilla), `GET /{id}/slots` (query: desde, hasta)
- [x] 5.3 Actualizar `backend/app/api/v1/__init__.py` exportando nuevos routers
- [x] 5.4 Tests integración endpoints: `pytest tests/api/v1/test_profesionales_admin.py -v`, `pytest tests/api/v1/test_profesionales_me.py -v`, `pytest tests/api/v1/test_profesionales_public.py -v`

## 6. Migración y Verificación

- [x] 6.1 Revisar migración generada: verificar orden FK, índices compuestos (`ix_profesional_usuario_activo`, `ix_servicio_profesional_activo`, `ix_disponibilidad_profesional_dia`, `ix_excepcion_profesional_fecha`), constraints (unicidad nombre servicio por profesional, check duracion > 0)
- [x] 6.2 Aplicar migración en BD limpia: `alembic upgrade head` → verificar esquema
- [x] 6.3 Verificar downgrade/upgrade limpio: `alembic downgrade base && alembic upgrade head` sin errores

## 7. Tests Completos y Calidad

- [x] 7.1 Tests unitarios models: `pytest tests/models/test_profesional.py -v`
- [x] 7.2 Tests unitarios repositories: `pytest tests/repositories/test_profesional_repo.py -v`
- [x] 7.3 Tests unitarios slot logic: `pytest tests/services/test_slot_service.py -v` (edge cases: excepciones, turnos ocupados, grilla vacía, rango fechas)
- [x] 7.5 Suite completa: `cd backend && pytest --cov=app --cov-report=term-missing --cov-fail-under=80`
- [x] 7.6 Lint y typecheck: `cd backend && ruff check app/` && `mypy app/`

## 8. Documentación y Verificación Final

- [x] 8.1 Verificar endpoints en Swagger `/docs` - todos documentados con ejemplos
- [x] 8.2 Probar flujo E2E manual: admin crea profesional → profesional configura servicios + grilla + excepción → público ve slots → cliente reserva (CU-03 futuro)
- [x] 8.2 Verificar RBAC: admin ve todo, profesional solo suyo, público solo lectura

## Workflow follow-up

- Ejecutar `/opsx-archive` para archivar este cambio tras verificación exitosa
- Ejecutar `/learn "CU-02 profesionales implementado: Models/Repos/Services/API para profesionales, servicios, disponibilidad, excepciones, slots. Algoritmo slots determinístico, RBAC 3 niveles, tests ≥80%, migración Alembic"` para guardar en Engram