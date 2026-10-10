# Especificación de Dominio: Profesionales y Servicios (CU-02, CU-10)

## Resumen

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