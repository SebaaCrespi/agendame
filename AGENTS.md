# AGENTS.md - Instrucciones para Agentes IA (OpenCode)

## Contexto del Proyecto

**Agendame** - Sistema de gestión de turnos multi-prestador con chatbot IA (LangChain + Groq).

Stack: React+Vite / FastAPI+SQLAlchemy / SQLite / OpenSpec (SDD) / OpenCode / Engram (memoria)

## Principios de Desarrollo

1. **Spec-Driven Development**: Cada cambio inicia con `/opsx-propose` → `/opsx-apply` → `/opsx-archive`
2. **Arquitectura Limpia**: Controllers → Services → Repositories (separación estricta)
3. **Tipado Estricto**: Python 3.12+ type hints, Pydantic v2, mypy strict
4. **Tests First**: Tests en `tests/` mirroring `app/` structure, pytest + httpx
5. **Memoria Persistente**: Usar Engram (`mem_save`, `mem_search`, `mem_context`) para decisiones, bugs, convenciones

## Estructura del Proyecto

```
agendame/
├── openspec/                 # Especificaciones (source of truth)
│   ├── specs/                # Specs actuales por dominio
│   │   ├── system/
│   │   ├── auth/
│   │   ├── profesionales/
│   │   ├── turnos/
│   │   └── chatbot/
│   ├── changes/              # Cambios activos (propuestas)
│   └── config.yaml
├── .opencode/                # Skills y comandos OpenCode
├── backend/                  # FastAPI App
│   ├── app/
│   │   ├── api/              # Controllers (endpoints)
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── profesionales.py
│   │   │   │   ├── turnos.py
│   │   │   │   └── chat.py
│   │   │   └── deps.py       # Dependencias (auth, db, etc.)
│   │   ├── core/             # Config, security, database
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/           # SQLAlchemy Models
│   │   │   ├── user.py
│   │   │   ├── profesional.py
│   │   │   ├── servicio.py
│   │   │   ├── disponibilidad.py
│   │   │   ├── turno.py
│   │   │   └── cliente.py
│   │   ├── schemas/          # Pydantic Schemas (request/response)
│   │   ├── services/         # Business Logic
│   │   │   ├── auth_service.py
│   │   │   ├── profesional_service.py
│   │   │   ├── turno_service.py
│   │   │   └── chatbot_service.py
│   │   ├── repositories/     # Data Access
│   │   │   ├── user_repo.py
│   │   │   ├── profesional_repo.py
│   │   │   ├── turno_repo.py
│   │   │   └── chat_repo.py
│   │   └── main.py           # FastAPI app factory
│   ├── tests/
│   ├── alembic/              # Migraciones
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/                 # React + Vite
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/         # API client
│   │   ├── hooks/
│   │   └── contexts/
│   ├── package.json
│   └── vite.config.ts
└── docker-compose.yml        # Dev environment
```

## Comandos OpenCode Disponibles

| Comando | Uso |
|---------|-----|
| `/opsx-propose "idea"` | Crear propuesta + specs delta |
| `/opsx-apply` | Implementar desde spec |
| `/opsx-archive` | Archivar cambio completado |
| `/opsx-explore` | Explorar idea antes de proponer |
| `/opsx-sync` | Sincronizar specs |
| `/opsx-update` | Actualizar skills/comandos |
| `/learn` | Capturar aprendizaje (Engram) |
| `/review` | Revisar items pendientes (Engram) |
| `/coach` | Coaching session (Engram) |

## Flujo de Trabajo Estándar

```
1. Leer specs relevantes en openspec/specs/<dominio>/
2. /opsx-propose "CU-XX: Descripción breve"
3. Revisar proposal.md + specs/ + design.md + tasks.md
4. /opsx-apply (en nueva sesión OpenCode)
5. Implementar siguiendo tasks.md
6. Tests pasan + lint + typecheck
7. /opsx-archive
8. /learn "Resumen de lo implementado y decisiones clave"
```

## Convenciones de Código

### Backend (Python)

```python
# Models: PascalCase, tablas snake_case plural
class Turno(Base): __tablename__ = "turnos"

# Schemas: <Entidad><Acción> - Create/Update/Response/List
class TurnoCreate(BaseModel): ...
class TurnoResponse(BaseModel): ...

# Services: <Entidad>Service - métodos verbosos
class TurnoService:
    async def crear_reserva_manual(self, ...) -> TurnoResponse: ...
    async def cancelar_turno_cliente(self, ...) -> bool: ...

# Repositories: <Entidad>Repo - CRUD + queries específicas
class TurnoRepo:
    async def get_by_id(self, id: int) -> Turno | None: ...
    async def get_slots_libres(self, prof_id: int, desde: date, hasta: date) -> List[Slot]: ...

# Endpoints: RESTful, plural, versionados
POST   /api/v1/turnos                    # Crear
GET    /api/v1/turnos/mis-turnos         # Listar míos
GET    /api/v1/turnos/{id}               # Detalle
PUT    /api/v1/turnos/{id}/cancelar      # Acción (sub-recurso)
```

### Frontend (TypeScript/React)

```typescript
// API Client: services/api.ts con axios + interceptors auth
// Hooks: useTurnos, useProfesionales, useAuth
// Components: PascalCase, colocados en components/<feature>/
// Pages: PascalCase en pages/
```

## Reglas de Engram (Memoria)

**SIEMPRE hacer `mem_save` tras:**
- Decisiones de arquitectura/stack
- Bugs encontrados y fix
- Convenciones acordadas
- Patrones que funcionan/no funcionan
- Comandos/configuraciones útiles

**AL INICIO de sesión:** `mem_context` para recuperar contexto

**AL FINAL de sesión:** `mem_session_summary` con logros

## Variables de Entorno (Backend)

```env
# .env en backend/
DATABASE_URL=sqlite:///./agendame.db
JWT_SECRET_KEY=dev-secret-change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7
GROQ_API_KEY=tu-groq-key
CHAT_MODEL=llama-3.3-70b-versatile
CORS_ORIGINS=http://localhost:5173
```

## Scripts Útiles

```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head          # Migraciones
uvicorn app.main:app --reload # Dev server
pytest -v                     # Tests
mypy app/                     # Type check
ruff check app/               # Lint

# Frontend
cd frontend
npm install
npm run dev                   # Vite dev server
npm run build                 # Production build
npm run lint                  # ESLint
```

## Debugging Común

| Problema | Solución |
|----------|----------|
| JWT invalid | Verificar `JWT_SECRET_KEY` igual en .env y tests |
| Slot ocupado | Verificar transacción DB + lock en `crear_turno` |
| Chatbot no responde | Verificar `GROQ_API_KEY`, logs LangChain |
| CORS error | `CORS_ORIGINS` incluye `http://localhost:5173` |
| Migración falla | `alembic downgrade -1` → fix model → `alembic revision --autogenerate` |

## Referencias Rápidas

- **Specs**: `openspec/specs/<dominio>/spec.md`
- **OpenSpec Docs**: https://openspec.dev
- **Engram Docs**: https://gentleman-programming-engram.mintlify.app
- **Groq API**: https://console.groq.com/docs
- **LangChain Tools**: https://python.langchain.com/docs/modules/agents/tools