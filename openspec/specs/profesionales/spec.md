# Especificación de Dominio: Profesionales y Servicios (CU-02, CU-03, CU-10)

## Purpose

Gestión de profesionales (proveedores/peluqueros), sus servicios ofrecidos y configuración de disponibilidad horaria. Cada profesional tiene su grilla aislada e independiente.

## Requisitos Funcionales

### RF-PROF-01: CRUD de Profesionales (Admin)
- **Descripción**: Administrador gestiona profesionales del sistema
- **Operaciones**:
  - **Crear**: Nombre, email (usuario asociado), teléfono, biografía, foto, activo
  - **Leer**: Listado paginado, detalle por ID
  - **Actualizar**: Todos los campos excepto email de usuario
  - **Eliminar**: Soft delete (marcar inactivo), solo si no tiene turnos futuros
- **Regla**: Al crear profesional → se crea usuario con rol PROVEEDOR

### RF-PROF-02: Configuración de Servicios por Profesional
- **Descripción**: Cada profesional define sus propios servicios
- **Campos**: Nombre, descripción, duración (minutos), precio, activo
- **Validaciones**: Duración > 0, precio >= 0, nombre único por profesional
- **Relación**: Servicio pertenece a UN profesional (aislamiento)

### RF-PROF-03: Configuración de Disponibilidad Horaria (Grilla)
- **Descripción**: Profesional define sus días y horarios de atención
- **Modelo**: Recurrencia semanal (lunes-domingo) + excepciones (feriados, vacaciones)
- **Campos por día**: Hora inicio, hora fin, activo (sí/no)
- **Slot duration**: Duración base del turno (ej. 30 min) - configurable por profesional
- **Excepciones**: Fechas específicas con horarios diferentes o cerrado

### RF-PROF-03b: Generación de Slots Disponibles
- **Descripción**: Calcular slots libres para un rango de fechas
- **Entrada**: profesional_id, fecha_inicio, fecha_fin
- **Salida**: Lista de slots {fecha, hora_inicio, hora_fin, disponible}
- **Lógica**: 
  - Generar slots según grilla semanal + excepciones
  - Restar turnos ya reservados (estado CONFIRMADO/PENDIENTE)
  - Restar bloques de mantenimiento del profesional

### RF-PROF-04: Perfil Público del Profesional
- **Descripción**: Vista de solo lectura para clientes
- **Incluye**: Nombre, foto, biografía, servicios (activos), grilla semanal resumida, rating promedio (futuro)

## Modelo de Datos (SQLAlchemy)

```python
class Profesional(Base):
    __tablename__ = "profesionales"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    telefono = Column(String(20))
    biografia = Column(Text)
    foto_url = Column(String(500))
    activo = Column(Boolean, default=True)
    slot_duracion_min = Column(Integer, default=30)  # duración base de slot
    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    usuario = relationship("User", back_populates="proveedor")
    servicios = relationship("Servicio", back_populates="profesional", cascade="all, delete-orphan")
    disponibilidades = relationship("Disponibilidad", back_populates="profesional", cascade="all, delete-orphan")
    turnos = relationship("Turno", back_populates="profesional")

class Servicio(Base):
    __tablename__ = "servicios"
    
    id = Column(Integer, primary_key=True, index=True)
    profesional_id = Column(Integer, ForeignKey("profesionales.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    duracion_min = Column(Integer, nullable=False)  # ej. 30, 45, 60
    precio = Column(Numeric(10, 2), nullable=False, default=0)
    activo = Column(Boolean, default=True)
    orden = Column(Integer, default=0)
    creado_en = Column(DateTime, default=datetime.utcnow)
    
    profesional = relationship("Profesional", back_populates="servicios")
    turnos = relationship("Turno", back_populates="servicio")

class Disponibilidad(Base):
    __tablename__ = "disponibilidades"
    
    id = Column(Integer, primary_key=True, index=True)
    profesional_id = Column(Integer, ForeignKey("profesionales.id"), nullable=False)
    dia_semana = Column(Integer, nullable=False)  # 0=Lunes ... 6=Domingo
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    activo = Column(Boolean, default=True)
    
    profesional = relationship("Profesional", back_populates="disponibilidades")

class ExcepcionDisponibilidad(Base):
    __tablename__ = "excepciones_disponibilidad"
    
    id = Column(Integer, primary_key=True, index=True)
    profesional_id = Column(Integer, ForeignKey("profesionales.id"), nullable=False)
    fecha = Column(Date, nullable=False, index=True)
    hora_inicio = Column(Time)  # None = día cerrado
    hora_fin = Column(Time)
    motivo = Column(String(200))  # "Vacaciones", "Feriado", "Mantenimiento"
    creado_en = Column(DateTime, default=datetime.utcnow)
    
    profesional = relationship("Profesional")
```

## Endpoints API

### Admin (rol ADMIN)
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/admin/profesionales` | Crear profesional + usuario |
| GET | `/admin/profesionales` | Listar (paginado, filtros) |
| GET | `/admin/profesionales/{id}` | Detalle profesional |
| PUT | `/admin/profesionales/{id}` | Actualizar profesional |
| DELETE | `/admin/profesionales/{id}` | Desactivar (soft delete) |

### Profesional (rol PROVEEDOR - solo suyo)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/profesionales/me` | Mi perfil profesional |
| PUT | `/profesionales/me` | Actualizar mi perfil |
| GET | `/profesionales/me/servicios` | Mis servicios |
| POST | `/profesionales/me/servicios` | Crear servicio |
| PUT | `/profesionales/me/servicios/{id}` | Actualizar servicio |
| DELETE | `/profesionales/me/servicios/{id}` | Desactivar servicio |
| GET | `/profesionales/me/disponibilidad` | Mi grilla semanal |
| PUT | `/profesionales/me/disponibilidad` | Actualizar grilla completa |
| POST | `/profesionales/me/excepciones` | Agregar excepción (vacaciones) |
| DELETE | `/profesionales/me/excepciones/{id}` | Eliminar excepción |

### Público (sin auth / CLIENTE)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/profesionales` | Listar profesionales activos (paginado) |
| GET | `/profesionales/{id}` | Perfil público + servicios + grilla |
| GET | `/profesionales/{id}/slots` | Slots disponibles (query: desde, hasta) |

## Reglas de Negocio

1. **Aislamiento**: Profesional solo ve/modifica SUS servicios, disponibilidad, turnos
2. **Consistencia**: No se puede eliminar profesional con turnos futuros confirmados
3. **Slots**: Duración del slot = MCM(duración_servicios) o slot_duracion_min del profesional
4. **Excepciones**: Tienen prioridad sobre grilla semanal
5. **Usuario vinculado**: Profesional ↔ User 1:1, rol PROVEEDOR obligatorio

## Criterios de Aceptación

1. Admin puede crear profesional → se crea usuario PROVEEDOR automáticamente
2. Profesional configura servicios: nombre, duración, precio
3. Profesional define grilla semanal (ej. Lun-Vie 9-13, 15-19; Sab 9-13)
4. Profesional agrega excepción: "2026-12-25 cerrado por Navidad"
5. GET `/profesionales/1/slots?desde=2026-10-15&hasta=2026-10-21` retorna slots libres
6. Slots excluyen turnos ya reservados y excepciones
7. Profesional A no ve servicios/grilla/turnos del Profesional B

## Requirements

<!-- Agregados por el change cu-04-reserva-manual (CU-04) -->

### Requirement: Listado público de profesionales con servicios
El listado público de profesionales SHALL devolver una lista paginada con solo los profesionales activos. Cada profesional SHALL incluir id, nombre, apellido, bio, foto, duración de slot y sus servicios activos (id, nombre, descripción, duración en minutos y precio en centavos).

#### Scenario: Listado con servicios
- **WHEN** un cliente autenticado consulta el listado y hay un profesional activo con dos servicios activos y uno inactivo
- **THEN** la respuesta incluye a ese profesional con sus dos servicios activos

#### Scenario: Profesional inactivo
- **WHEN** existe un profesional inactivo
- **THEN** no aparece en el listado público

### Requirement: Listado público sin datos privados
El listado público y el detalle público de un profesional SHALL NOT exponer su email ni el id de su usuario.

#### Scenario: Sin email
- **WHEN** un cliente consulta el listado público
- **THEN** ningún profesional de la respuesta tiene los campos email ni user_id

### Requirement: Grilla sin turnos huérfanos
Al reemplazar la grilla semanal, el sistema SHALL rechazar el cambio con 409 si algún turno futuro propio en estado PENDIENTE, CONFIRMADO o EN_CURSO quedaría fuera del horario del nuevo día correspondiente, salvo que ese día tenga una excepción que lo cubra. La respuesta SHALL indicar cuántos turnos quedarían afuera y sus fechas. Si no hay conflicto, la grilla se reemplaza completa.

#### Scenario: Acortar un día sin turnos afectados
- **WHEN** el proveedor cambia los lunes de 09:00–18:00 a 09:00–13:00 y no tiene turnos futuros los lunes después de las 13:00
- **THEN** la grilla se guarda

#### Scenario: Acortar un día con un turno afectado
- **WHEN** el proveedor tiene un turno CONFIRMADO el próximo lunes a las 15:00 y cambia los lunes a 09:00–13:00
- **THEN** el sistema responde 409 indicando 1 turno afectado y su fecha, y la grilla no cambia

#### Scenario: Dejar de atender un día
- **WHEN** el proveedor tiene un turno PENDIENTE el próximo sábado y quita el sábado de la grilla
- **THEN** el sistema responde 409

#### Scenario: Turnos cancelados o pasados no bloquean
- **WHEN** los únicos turnos fuera del nuevo horario están cancelados o ya terminaron
- **THEN** la grilla se guarda

### Requirement: Excepción sin turnos huérfanos
Al agregar una excepción, el sistema SHALL rechazarla con 409 si algún turno futuro propio en estado PENDIENTE, CONFIRMADO o EN_CURSO de esa fecha quedaría fuera de ella: cualquier turno del día para CERRADO, o los que no entren en el horario especial para HORARIO_ESPECIAL.

#### Scenario: Cerrar un día con turnos
- **WHEN** el proveedor tiene un turno CONFIRMADO el 20/11 y agrega una excepción CERRADO para el 20/11
- **THEN** el sistema responde 409 y la excepción no se crea

#### Scenario: Horario especial compatible
- **WHEN** el proveedor tiene un turno el 20/11 de 10:00 a 10:30 y agrega un horario especial de 09:00 a 12:00 para ese día
- **THEN** la excepción se crea

### Requirement: Configuración del proveedor desde la interfaz
La aplicación SHALL permitir al proveedor editar su perfil (nombre, apellido, teléfono, biografía, foto y duración base del slot), administrar sus servicios (crear, editar y desactivar) y configurar su disponibilidad (grilla semanal con un horario por día y excepciones). Cada formulario SHALL mostrar el error que devuelva el sistema, incluido el aviso de turnos afectados.

#### Scenario: Crear un servicio
- **WHEN** el proveedor crea "Barba" de 20 minutos a $3.000
- **THEN** el servicio aparece en su lista y en la reserva del cliente

#### Scenario: Nombre de servicio repetido
- **WHEN** el proveedor crea un servicio con el nombre de otro servicio suyo
- **THEN** la página muestra el error y no crea nada

#### Scenario: Configurar la semana
- **WHEN** el proveedor marca martes a sábado de 10:00 a 19:00 y guarda
- **THEN** el cliente ve slots solo esos días y en ese horario

#### Scenario: Cambio bloqueado por turnos
- **WHEN** el proveedor intenta cerrar un día que tiene turnos
- **THEN** la página muestra cuántos turnos quedarían afuera y no cambia la configuración

### Requirement: Baja de profesional con turnos pendientes
El sistema SHALL rechazar con 409 la desactivación de un profesional que tenga turnos PENDIENTE, CONFIRMADO o EN_CURSO cuya hora de fin todavía no llegó según la hora del negocio, tanto por `DELETE /admin/profesionales/{id}` como por `PUT /admin/profesionales/{id}` con `activo: false`. La respuesta SHALL indicar cuántos turnos lo impiden. Reactivar un profesional SHALL estar siempre permitido.

#### Scenario: Baja por edición con turnos
- **WHEN** el admin envía `activo: false` para un profesional con un turno CONFIRMADO mañana
- **THEN** el sistema responde 409 y el profesional sigue activo

#### Scenario: Baja con turnos ya terminados
- **WHEN** el profesional solo tiene turnos CONFIRMADO que terminaron hoy más temprano
- **THEN** la desactivación se acepta

#### Scenario: Reactivar
- **WHEN** el admin envía `activo: true` para un profesional inactivo
- **THEN** el profesional vuelve a figurar en el listado público

### Requirement: Gestión de profesionales desde la interfaz
La aplicación SHALL permitir al administrador listar los profesionales (paginado, con búsqueda por nombre y filtro por activos o inactivos), crear uno con su usuario PROVEEDOR, editar sus datos, desactivarlo y reactivarlo. Los errores del sistema (email ya registrado, turnos que impiden la baja) SHALL mostrarse en la pantalla.

#### Scenario: Alta de profesional
- **WHEN** el admin crea a "Lucía Díaz" con email y contraseña temporal
- **THEN** Lucía aparece activa en la lista y puede iniciar sesión como proveedor

#### Scenario: Email repetido
- **WHEN** el admin crea un profesional con un email ya registrado
- **THEN** la pantalla muestra el error y no crea nada

#### Scenario: Baja impedida
- **WHEN** el admin desactiva a un profesional con turnos pendientes
- **THEN** la pantalla muestra cuántos turnos lo impiden y el profesional sigue activo

#### Scenario: Grillas independientes
- **WHEN** el admin crea un profesional nuevo
- **THEN** el profesional empieza sin servicios ni grilla y no ve los de otros profesionales

### Requirement: Listado público de profesionales sin sesión
Los endpoints públicos de `/profesionales` (listado, detalle, servicios, grilla, excepciones y slots) SHALL responder sin sesión. Siguen devolviendo solo profesionales activos y sin datos de contacto privados.

#### Scenario: Visitante ve profesionales
- **WHEN** un visitante sin token pide `GET /profesionales`
- **THEN** el sistema responde 200 con los profesionales activos y sus servicios activos
