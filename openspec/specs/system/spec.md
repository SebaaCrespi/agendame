# Índice de Especificaciones - Agendame

## Estructura de Dominios

```
openspec/specs/
├── system/
│   └── spec.md              # Visión general del sistema (este archivo)
├── auth/
│   └── spec.md              # CU-01: Autenticación y Autorización
├── profesionales/
│   └── spec.md              # CU-02, CU-10: Profesionales, Servicios, Disponibilidad
├── turnos/
│   └── spec.md              # CU-03, CU-04, CU-06, CU-07, CU-08, CU-09: Turnos y Reservas
└── chatbot/
    └── spec.md              # CU-05, CU-06: Asistente Virtual (LangChain + Groq)
```

## Resumen de Casos de Uso por Dominio

| Dominio | Casos de Uso | Endpoints Clave |
|---------|-------------|-----------------|
| **auth** | CU-01 | `/auth/register`, `/auth/login`, `/auth/me` |
| **profesionales** | CU-02, CU-10 | `/admin/profesionales`, `/profesionales/me/*`, `/profesionales/{id}/slots` |
| **turnos** | CU-03, CU-04, CU-06, CU-07, CU-08, CU-09 | `/turnos/disponibilidad`, `/turnos`, `/profesionales/me/turnos` |
| **chatbot** | CU-05, CU-06 | `/chat/message`, `/internal/turnos/reservar` |

## Orden de Implementación Sugerido

1. **auth** - Base para todo (usuarios, roles, JWT)
2. **profesionales** - Entidades core (profesionales, servicios, grillas)
3. **turnos** - Lógica de negocio central (reservas, estados, historial)
4. **chatbot** - Capa de IA sobre APIs existentes

## Convenciones Transversales

- **Arquitectura**: Controllers → Services → Repositories
- **DB**: SQLite + SQLAlchemy, migraciones con Alembic
- **Auth**: JWT HS256, access 24h + refresh 7d rotativo
- **Validación**: Pydantic v2 en schemas request/response
- **Errores**: RFC 7807 (Problem Details) + códigos HTTP estándar
- **Testing**: pytest, coverage ≥ 80% en services
- **Documentación**: OpenAPI/Swagger auto-generado en `/docs`

## Variables de Entorno Requeridas

```env
# App
APP_ENV=development
APP_SECRET_KEY=super-secret-key-change-in-production
APP_CORS_ORIGINS=http://localhost:5173

# Database
DATABASE_URL=sqlite:///./agendame.db

# Auth
JWT_SECRET_KEY=jwt-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Groq / Chatbot
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
CHAT_MODEL=llama-3.3-70b-versatile
CHAT_TEMPERATURE=0.1

# Frontend (Vite)
VITE_API_URL=http://localhost:8000
```