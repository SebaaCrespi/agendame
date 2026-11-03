# Spec Delta

## MODIFIED Requirements

### Requirement: Registro de Usuario (RF-AUTH-01)
El sistema SHALL permitir el registro de nuevos usuarios con email, contraseña, nombre y rol (CLIENTE, PROVEEDOR, ADMIN).

#### Scenario: Registro exitoso como CLIENTE
- **WHEN** usuario envía POST /auth/register con email único, password ≥8 chars, nombre, rol=CLIENTE
- **THEN** sistema crea usuario, retorna 201 con JWT access token, refresh token y datos de usuario (sin password_hash)

#### Scenario: Registro exitoso como PROVEEDOR
- **WHEN** usuario envía POST /auth/register con rol=PROVEEDOR
- **THEN** sistema crea usuario con rol PROVEEDOR, retorna 201 con tokens y datos

#### Scenario: Email duplicado
- **WHEN** usuario intenta registrar email ya existente
- **THEN** sistema retorna 409 Conflict con detalle "Email ya registrado"

#### Scenario: Password inválido
- **WHEN** usuario envía password con menos de 8 caracteres
- **THEN** sistema retorna 422 Validation Error

#### Scenario: Rol inválido
- **WHEN** usuario envía rol no permitido (ej. "SUPER_ADMIN")
- **THEN** sistema retorna 422 Validation Error

### Requirement: Inicio de Sesión (RF-AUTH-02)
El sistema SHALL autenticar usuarios existentes y generar tokens de acceso y renovación.

#### Scenario: Login exitoso
- **WHEN** usuario envía POST /auth/login con email y password correctos
- **THEN** sistema retorna 200 con access token (24h), refresh token (7d rotativo) y datos de usuario + rol

#### Scenario: Credenciales inválidas
- **WHEN** usuario envía email correcto pero password incorrecto
- **THEN** sistema retorna 401 Unauthorized con detalle "Credenciales inválidas"

#### Scenario: Usuario inactivo
- **WHEN** usuario con activo=false intenta loguearse
- **THEN** sistema retorna 403 Forbidden con detalle "Usuario inactivo"

#### Scenario: Rate limiting login
- **WHEN** se superan 5 intentos de login por minuto desde misma IP
- **THEN** sistema retorna 429 Too Many Requests

### Requirement: Renovación de Token (RF-AUTH-03)
El sistema SHALL permitir obtener nuevo access token usando refresh token válido con rotación.

#### Scenario: Refresh exitoso
- **WHEN** cliente envía POST /auth/refresh con refresh token válido
- **THEN** sistema retorna 200 con nuevo access token (24h) y nuevo refresh token (7d), invalida el anterior

#### Scenario: Refresh token expirado
- **WHEN** cliente usa refresh token con más de 7 días
- **THEN** sistema retorna 401 Unauthorized "Refresh token expirado"

#### Scenario: Refresh token reutilizado (rotación)
- **WHEN** cliente usa un refresh token que ya fue rotado
- **THEN** sistema retorna 401 Unauthorized "Token inválido" e invalida la cadena completa

### Requirement: Middleware de Validación JWT (RF-AUTH-04)
El sistema SHALL validar JWT en rutas protegidas mediante middleware que extrae user_id y rol.

#### Scenario: Token válido
- **WHEN** request incluye Authorization: Bearer <jwt_válido>
- **THEN** middleware valida firma HS256, expiración, extrae user_id y rol, inyecta en request.state.current_user

#### Scenario: Token sin header Authorization
- **WHEN** request a ruta protegida sin header Authorization
- **THEN** sistema retorna 401 Unauthorized "No autenticado"

#### Scenario: Token malformado
- **WHEN** request incluye Authorization: Bearer <token_inválido>
- **THEN** sistema retorna 401 Unauthorized "Token inválido"

#### Scenario: Token expirado
- **WHEN** request incluye access token con exp < now()
- **THEN** sistema retorna 401 Unauthorized "Token expirado"

### Requirement: Control de Acceso por Rol RBAC (RF-AUTH-05)
El sistema SHALL restringir endpoints según rol: ADMIN (total), PROVEEDOR (solo propios), CLIENTE (solo propios).

#### Scenario: ADMIN accede a endpoint admin
- **WHEN** usuario ADMIN accede a GET /admin/profesionales
- **THEN** sistema permite acceso (200)

#### Scenario: PROVEEDOR intenta acceder a endpoint admin
- **WHEN** usuario PROVEEDOR accede a GET /admin/profesionales
- **THEN** sistema retorna 403 Forbidden "Acceso denegado: se requiere rol ADMIN"

#### Scenario: PROVEEDOR accede a sus recursos
- **WHEN** usuario PROVEEDOR accede a GET /profesionales/me/servicios
- **THEN** sistema permite acceso y filtra solo sus servicios

#### Scenario: CLIENTE accede a sus turnos
- **WHEN** usuario CLIENTE accede a GET /turnos/mis-turnos
- **THEN** sistema permite acceso y filtra solo sus turnos

#### Scenario: CLIENTE intenta acceder a recursos de profesional
- **WHEN** usuario CLIENTE accede a GET /profesionales/me/servicios
- **THEN** sistema retorna 403 Forbidden "Acceso denegado: se requiere rol PROVEEDOR"