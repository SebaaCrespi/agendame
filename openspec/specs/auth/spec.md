# Especificación de Dominio: Autenticación y Autorización (CU-01)

## Resumen

Sistema de registro e inicio de sesión con discriminación de roles (Cliente, Proveedor, Administrador) usando JWT para sesiones stateless.

## Requisitos Funcionales

### RF-AUTH-01: Registro de Usuario
- **Descripción**: Permitir registro de nuevos usuarios con email, contraseña y rol
- **Campos**: email (único), password (hash bcrypt), nombre, rol (CLIENTE|PROVEEDOR|ADMIN)
- **Validaciones**: Email único, password mínimo 8 chars, rol válido
- **Resultado**: Usuario creado, retorna JWT + datos de usuario (sin password)

### RF-AUTH-02: Inicio de Sesión
- **Descripción**: Autenticar usuario existente y generar token de acceso
- **Entrada**: email, password
- **Salida**: JWT (expiración 24h), refresh token (7 días), datos de usuario + rol
- **Manejo de errores**: Credenciales inválidas (401), usuario inactivo (403)

### RF-AUTH-03: Renovación de Token
- **Descripción**: Obtener nuevo access token usando refresh token
- **Entrada**: refresh token válido
- **Salida**: Nuevo access token + nuevo refresh token (rotación)

### RF-AUTH-04: Validación de Token (Middleware)
- **Descripción**: Middleware FastAPI para validar JWT en rutas protegidas
- **Comportamiento**: Extraer token de header `Authorization: Bearer <token>`, validar firma, expiración, extraer user_id y rol
- **Inyección**: Disponibilizar `current_user` en request.state

### RF-AUTH-05: Control de Acceso por Rol (RBAC)
- **Descripción**: Decoradores/dependencies para restringir endpoints por rol
- **Roles**: `CLIENTE`, `PROVEEDOR`, `ADMIN`
- **Reglas**:
  - ADMIN: acceso total
  - PROVEEDOR: solo sus recursos (grilla, turnos, servicios)
  - CLIENTE: solo sus reservas e historial

## Modelo de Datos (SQLAlchemy)

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    rol = Column(Enum(UserRole), nullable=False, default=UserRole.CLIENTE)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    proveedor = relationship("Proveedor", back_populates="usuario", uselist=False)
    cliente = relationship("Cliente", back_populates="usuario", uselist=False)
```

## Endpoints API

| Método | Ruta | Descripción | Auth | Roles |
|--------|------|-------------|------|-------|
| POST | `/auth/register` | Registrar usuario | No | - |
| POST | `/auth/login` | Iniciar sesión | No | - |
| POST | `/auth/refresh` | Renovar token | No | - |
| GET | `/auth/me` | Usuario actual | Sí | Todos |
| PUT | `/auth/me` | Actualizar perfil | Sí | Todos |

## Seguridad

- Passwords: bcrypt (cost factor 12)
- JWT: HS256, secret desde variable de entorno
- Access token: 24h, Refresh token: 7d (rotación)
- Rate limiting: 5 req/min en login/register
- CORS configurado para frontend origin

## Criterios de Aceptación

1. Usuario puede registrarse como CLIENTE o PROVEEDOR (ADMIN solo por seed/CLI)
2. Login retorna JWT válido y refresh token
3. Token expirado → 401, refresh token válido → nuevo access token
4. Middleware rechaza requests sin token o token inválido
5. Endpoint `/proveedores/mi-grilla` solo accesible por PROVEEDOR dueño
6. Endpoint `/admin/proveedores` solo accesible por ADMIN