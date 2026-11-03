# Spec Delta

## Purpose

Proporciona la configuración base, conexión a base de datos, seguridad y punto de entrada de la aplicación FastAPI que sirve como fundación para todos los dominios (auth, profesionales, turnos, chatbot).

## ADDED Requirements

### Requirement: Configuración Centralizada
El sistema SHALL cargar configuración desde variables de entorno usando Pydantic Settings con validación de tipos.

#### Scenario: Configuración válida
- **WHEN** aplicación inicia con .env completo
- **THEN** settings carga DATABASE_URL, JWT_SECRET_KEY, CORS_ORIGINS, GROQ_API_KEY sin errores

#### Scenario: Variable requerida faltante
- **WHEN** falta JWT_SECRET_KEY en entorno
- **THEN** aplicación falla al iniciar con error claro de configuración

### Requirement: Conexión a Base de Datos SQLite + SQLAlchemy
El sistema SHALL proveer sesión de base de datos asíncrona con SQLAlchemy 2.0 y migraciones Alembic.

#### Scenario: Sesión DB exitosa
- **WHEN** endpoint usa dependencia get_db
- **THEN** se provee AsyncSession transaccional con commit/rollback automático

#### Scenario: Migración inicial
- **WHEN** se ejecuta alembic upgrade head
- **THEN** se crean tablas users, profesionales, servicios, disponibilidades, excepciones_disponibilidad, turnos, clientes

### Requirement: Seguridad y Utilidades Criptográficas
El sistema SHALL proveer hashing bcrypt (cost 12), JWT HS256, y utilidades de validación de password.

#### Scenario: Hash password
- **WHEN** servicio llama hash_password("mipassword123")
- **THEN** retorna hash bcrypt verificable con verify_password

#### Scenario: Crear access token
- **WHEN** servicio llama create_access_token(data={"sub": "1", "rol": "CLIENTE"})
- **THEN** retorna JWT HS256 firmado con expiración 24h

#### Scenario: Crear refresh token
- **WHEN** servicio llama create_refresh_token(data={"sub": "1"})
- **THEN** retorna JWT HS256 firmado con expiración 7d y claim "type": "refresh"

### Requirement: Manejo de Errores Estándar (RFC 7807)
El sistema SHALL retornar errores en formato Problem Details (RFC 7807) con códigos HTTP apropiados.

#### Scenario: Error de validación
- **WHEN** request falla validación Pydantic
- **THEN** retorna 422 con {type, title, status, detail, instance}

#### Scenario: Error de negocio
- **WHEN** servicio lanza BusinessException("Slot no disponible")
- **THEN** retorna 409 con detail "Slot no disponible"

#### Scenario: Error interno no controlado
- **WHEN** ocurre excepción no manejada
- **THEN** retorna 500 con detail genérico, loggea stack trace completo

### Requirement: Health Check y CORS
El sistema SHALL exponer endpoint de salud y configurar CORS para origen del frontend.

#### Scenario: Health check
- **WHEN** GET /health
- **THEN** retorna 200 {"status": "ok", "version": "1.0.0"}

#### Scenario: CORS configurado
- **WHEN** frontend en http://localhost:5173 hace request a API
- **THEN** respuesta incluye Access-Control-Allow-Origin: http://localhost:5173

### Requirement: Punto de Entrada FastAPI
El sistema SHALL crear app FastAPI con routers versionados (/api/v1), docs en /docs, lifespan para startup/shutdown.

#### Scenario: App arranca
- **WHEN** uvicorn app.main:app --reload
- **THEN** servidor inicia en puerto 8000, docs accesible en /docs, routers montados

#### Scenario: Router auth montado
- **WHEN** app incluye router de auth
- **THEN** endpoints disponibles en /api/v1/auth/*