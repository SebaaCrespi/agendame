# Agendame Backend

Backend API for Agendame - Sistema de gestión de turnos multi-prestador.

## Stack

- **FastAPI** - Modern web framework
- **SQLAlchemy 2.0** - Async ORM
- **SQLite** - Database (dev)
- **Alembic** - Migrations
- **Pydantic v2** - Validation
- **python-jose** - JWT
- **passlib[bcrypt]** - Password hashing
- **slowapi** - Rate limiting
- **pytest** - Testing

## Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your settings (generate JWT_SECRET_KEY with: openssl rand -hex 32)

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLAlchemy async database URL | `sqlite+aiosqlite:///./agendame.db` |
| `JWT_SECRET_KEY` | Secret key for JWT signing (min 32 chars) | **Required** |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | `1440` (24h) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | `7` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:5173"]` |
| `GROQ_API_KEY` | Groq API key for chatbot | - |
| `CHAT_MODEL` | Groq model name | `llama-3.3-70b-versatile` |
| `RATE_LIMIT_REQUESTS` | Max requests per window | `5` |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate limit window | `60` |

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login user |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user |
| PUT | `/api/v1/auth/me` | Update current user |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

### Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing --cov-fail-under=80

# Run specific test file
pytest tests/test_auth.py -v

# Run unit tests only
pytest -m unit -v

# Run integration tests only
pytest -m integration -v
```

## Code Quality

```bash
# Lint
ruff check app/

# Format
ruff format app/

# Type check
mypy app/
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py          # Auth endpoints
│   │   │   └── __init__.py
│   │   ├── deps.py              # Dependencies (auth, RBAC, rate limit)
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py            # Settings
│   │   ├── database.py          # DB connection
│   │   ├── security.py          # JWT, password hashing
│   │   ├── exceptions.py        # RFC 7807 errors
│   │   └── __init__.py
│   ├── models/
│   │   ├── user.py              # User, RefreshToken, UserRole
│   │   ├── profesional.py       # Profesional (placeholder)
│   │   ├── cliente.py           # Cliente (placeholder)
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── auth.py              # Pydantic schemas
│   │   └── __init__.py
│   ├── services/
│   │   ├── auth_service.py      # Auth business logic
│   │   └── __init__.py
│   ├── repositories/
│   │   ├── user_repo.py         # User data access
│   │   └── __init__.py
│   └── main.py                  # FastAPI app factory
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   ├── test_auth.py             # Auth endpoint tests
│   ├── test_deps.py             # Dependency tests
│   ├── test_security.py         # Security unit tests
│   ├── test_exceptions.py       # Exception tests
│   └── test_main.py             # App tests
├── alembic/
│   ├── versions/                # Migration files
│   ├── env.py                   # Alembic async config
│   └── script.py.mako           # Migration template
├── requirements.txt
├── pyproject.toml
├── alembic.ini
└── .env.example
```

## Architecture

```
Controller (api/v1/) → Service (services/) → Repository (repositories/)
                                    ↓
                              Models (models/)
                                    ↓
                              Database (SQLAlchemy)
```

## Authentication Flow

1. **Register** → Returns access token (24h) + refresh token (7d)
2. **Login** → Returns access token (24h) + refresh token (7d)
3. **Access protected routes** → Include `Authorization: Bearer <access_token>`
4. **Refresh** → POST `/auth/refresh` with refresh token → Returns new token pair (rotation)
5. **Logout** → Client discards tokens (server-side: refresh token revoked on rotation)

## Rate Limiting

- Register: 5 requests/minute per IP
- Login: 5 requests/minute per IP

## RBAC

Roles: `CLIENTE`, `PROVEEDOR`, `ADMIN`

Dependencies:
- `get_current_user` - Any authenticated user
- `require_roles(*roles)` - Check user has one of allowed roles
- `require_admin` - Admin only
- `require_proveedor` - Proveedor or Admin
- `require_cliente` - Cliente or Admin

## Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Show current revision
alembic current
```