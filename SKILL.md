# SKILL.md - Skills Personalizadas para Agendame

## Skills Disponibles

Este documento define skills (habilidades) reutilizables para el desarrollo de Agendame con OpenCode.

---

## 1. skill: `crear-endpoint-crud`

**Descripción**: Genera endpoint REST completo (Controller + Service + Repository + Schemas + Tests) para una entidad.

**Uso**: `/skill crear-endpoint-crud Entidad [campos]`

**Parámetros**:
- `entidad`: Nombre singular PascalCase (ej. `Profesional`, `Servicio`)
- `campos`: Lista opcional `campo:tipo` (ej. `nombre:str precio:float activo:bool`)

**Genera**:
```
backend/app/api/v1/<entidad_lower>.py          # Controller
backend/app/services/<entidad_lower>_service.py # Service
backend/app/repositories/<entidad_lower>_repo.py # Repository
backend/app/schemas/<entidad_lower>.py          # Schemas (Create/Update/Response/List)
backend/tests/test_<entidad_lower>.py           # Tests CRUD
```

**Convenciones**:
- Router prefix: `/api/v1/<entidad_plural>`
- Tags: `[Entidad]`
- Auth: JWT requerido, RBAC por rol
- Paginación: `Page[Response]` con `limit/offset`
- Filtros: Query params tipados

---

## 2. skill: `crear-modelo-sqlalchemy`

**Descripción**: Crea modelo SQLAlchemy + migración Alembic + repo base.

**Uso**: `/skill crear-modelo-sqlalchemy Entidad campos relaciones`

**Parámetros**:
- `entidad`: Nombre modelo
- `campos`: `campo:tipo:constraints` (ej. `email:str:unique,index nombre:str:index`)
- `relaciones`: `relacion:Modelo:tipo` (ej. `usuario:User:one-to-one profesional:Profesional:one-to-many`)

**Genera**:
- Modelo en `backend/app/models/<entidad_lower>.py`
- Migración en `backend/alembic/versions/`
- Repository base en `backend/app/repositories/<entidad_lower>_repo.py`

---

## 3. skill: `implementar-chatbot-tool`

**Descripción**: Implementa una tool/function para el chatbot LangChain + Groq.

**Uso**: `/skill implementar-chatbot-tool nombre_tool descripcion parametros retorno`

**Parámetros**:
- `nombre_tool`: snake_case (ej. `consultar_disponibilidad`)
- `descripcion`: Para el LLM (docstring)
- `parametros`: JSON Schema de entrada
- `retorno`: JSON Schema de salida

**Genera**:
- Tool en `backend/app/chatbot/tools/<nombre_tool>.py`
- Registro en `backend/app/chatbot/tools/__init__.py`
- Test en `backend/tests/chatbot/test_tools.py`

**Ejemplo**:
```python
@tool
async def consultar_disponibilidad(
    profesional_id: int,
    fecha_inicio: str,  # YYYY-MM-DD
    fecha_fin: str,
    servicio_id: int | None = None
) -> dict:
    """Retorna slots libres agrupados por fecha para un profesional."""
    ...
```

---

## 4. skill: `configurar-auth-jwt`

**Descripción**: Configura autenticación JWT completa (login, register, refresh, middleware, RBAC).

**Uso**: `/skill configurar-auth-jwt`

**Genera/Actualiza**:
- `backend/app/core/security.py` (hash, create/verify token)
- `backend/app/api/v1/auth.py` (endpoints)
- `backend/app/api/deps.py` (dependencies: `get_current_user`, `require_roles`)
- `backend/app/models/user.py` (si no existe)
- Tests de auth

**Roles soportados**: `CLIENTE`, `PROVEEDOR`, `ADMIN`

---

## 5. skill: `generar-migracion`

**Descripción**: Crea y aplica migración Alembic tras cambios en modelos.

**Uso**: `/skill generar-migracion "mensaje descriptivo"`

**Ejecuta**:
```bash
cd backend
alembic revision --autogenerate -m "mensaje"
alembic upgrade head
```

**Valida**: Modelos importados en `alembic/env.py` target_metadata

---

## 6. skill: `test-endpoint`

**Descripción**: Genera tests completos para un endpoint (happy path + edge cases + auth).

**Uso**: `/skill test-endpoint METODO /ruta/endpoint`

**Genera** en `backend/tests/test_<feature>.py`:
- Test 200/201 success
- Test 400 validation error
- Test 401 unauthorized
- Test 403 forbidden (roles)
- Test 404 not found
- Test 409 conflict (unicidad)

---

## 7. skill: `setup-proyecto-inicial`

**Descripción**: Bootstrap completo del proyecto backend + frontend.

**Uso**: `/skill setup-proyecto-inicial`

**Ejecuta**:
1. Estructura de carpetas backend/frontend
2. `pyproject.toml` + `requirements.txt` (FastAPI, SQLAlchemy, Alembic, Pydantic, Python-JOSE, Passlib, PyTest, Ruff, MyPy)
3. `package.json` + `vite.config.ts` (React, TypeScript, Tailwind, Axios, React Router)
4. `docker-compose.yml` (PostgreSQL opcional, Redis para sessions chatbot)
5. `.env.example` con todas las variables
6. `alembic.ini` + `alembic/env.py` configurado
7. `backend/app/main.py` con CORS, lifespan, routers
8. Health check endpoint `/health`

---

## Cómo Usar Skills

En OpenCode chat:
```
/skill crear-endpoint-crud Profesional "nombre:str telefono:str biografia:text foto_url:str activo:bool slot_duracion_min:int"
```

O combinar:
```
/opsx-propose "CU-02: CRUD Profesionales y Servicios"
# El agente usará skills internamente para generar código
```

## Skills de OpenSpec (Ya Instaladas)

| Skill | Comando | Descripción |
|-------|---------|-------------|
| `openspec-new-change` | `/opsx-propose` | Nueva propuesta + artifacts |
| `openspec-propose` | `/opsx-propose` | Alias |
| `openspec-continue-change` | `/opsx-continue` | Continuar cambio existente |
| `openspec-explore` | `/opsx-explore` | Explorar idea |
| `openspec-apply-change` | `/opsx-apply` | Implementar spec |
| `openspec-verify-change` | `/opsx-verify` | Verificar implementación |
| `openspec-sync-specs` | `/opsx-sync` | Sincronizar specs |
| `openspec-archive-change` | `/opsx-archive` | Archivar cambio |

## Crear Nueva Skill

1. Crear archivo en `.opencode/skills/<nombre>.md`
2. Seguir formato: descripción, parámetros, pasos, output
3. Recargar: `/opsx-update`