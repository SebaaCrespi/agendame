# Especificación de Dominio: Turnos y Reservas (CU-03, CU-04, CU-06, CU-07, CU-08, CU-09)

## Resumen

Gestión completa del ciclo de vida de turnos: consulta de disponibilidad, reserva manual, reserva por chatbot, gestión por profesional, cancelación/reasignación e historial.

## Requisitos Funcionales

### RF-TURNO-01: Consulta de Disponibilidad (Público/Cliente)
- **Descripción**: Ver profesionales y sus slots disponibles en rango de fechas
- **Entrada**: fecha_inicio, fecha_fin, profesional_id (opcional), servicio_id (opcional)
- **Salida**: Lista de profesionales con sus slots libres agrupados por fecha
- **Filtros**: Por profesional, por servicio, por fecha, solo con disponibilidad

### RF-TURNO-02: Reserva Manual (Frontend)
- **Actor**: Cliente (autenticado)
- **Flujo**:
  1. Seleccionar profesional
  2. Seleccionar servicio (define duración)
  3. Seleccionar fecha → ver slots libres
  4. Seleccionar hora → confirmar
- **Validaciones**: Slot libre, servicio pertenece al profesional, cliente autenticado
- **Resultado**: Turno creado en estado PENDIENTE → CONFIRMADO automáticamente
- **Notificación**: (Futuro) Email/WS al cliente y profesional

### RF-TURNO-03: Gestión de Turnos por Profesional
- **Actor**: Proveedor (dueño de los turnos)
- **Vista**: Grilla semanal/mensual con turnos coloreados por estado
- **Filtros**: Por fecha, estado, cliente, servicio
- **Acciones**: Ver detalle, cambiar estado (CONFIRMADO → EN_CURSO → FINALIZADO), agregar nota interna

### RF-TURNO-04: Cancelación de Turno
- **Por Cliente**: Solo turnos futuros (> 2h de antelación configurable), estado → CANCELADO_CLIENTE
- **Por Profesional**: Cualquier turno futuro, estado → CANCELADO_PROVEEDOR, motivo obligatorio
- **Efecto**: Slot queda libre inmediatamente
- **Historial**: Se registra quién canceló, cuándo y motivo

### RF-TURNO-05: Reasignación de Turno (Profesional)
- **Descripción**: Profesional mueve turno a otro slot libre suyo
- **Validaciones**: Nuevo slot libre, mismo servicio (misma duración), turno futuro
- **Registro**: Auditoría con slot anterior/nuevo, motivo

### RF-TURNO-06: Historial de Turnos
- **Cliente**: Ver sus turnos (pasados, activos, cancelados) con filtros
- **Profesional**: Ver todos sus turnos con filtros avanzados
- **Estados**: PENDIENTE, CONFIRMADO, EN_CURSO, FINALIZADO, CANCELADO_CLIENTE, CANCELADO_PROVEEDOR, NO_ASISTIO

### RF-TURNO-07: Reserva por Chatbot (Integración CU-06)
- **Entrada desde Chatbot**: cliente_id, profesional_id, servicio_id, fecha, hora_inicio
- **Validación interna**: Mismas que reserva manual
- **Salida**: Turno creado + datos para respuesta conversacional

## Modelo de Datos (SQLAlchemy)

```python
class TurnoEstado(enum.Enum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    EN_CURSO = "en_curso"
    FINALIZADO = "finalizado"
    CANCELADO_CLIENTE = "cancelado_cliente"
    CANCELADO_PROVEEDOR = "cancelado_proveedor"
    NO_ASISTIO = "no_asistio"

class Turno(Base):
    __tablename__ = "turnos"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    profesional_id = Column(Integer, ForeignKey("profesionales.id"), nullable=False)
    servicio_id = Column(Integer, ForeignKey("servicios.id"), nullable=False)
    
    fecha = Column(Date, nullable=False, index=True)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)  # calculada: inicio + duracion_servicio
    
    estado = Column(Enum(TurnoEstado), default=TurnoEstado.PENDIENTE, nullable=False, index=True)
    notas_cliente = Column(Text)           # notas del cliente al reservar
    notas_profesional = Column(Text)       # notas internas del profesional
    cancelado_por = Column(String(20))     # "cliente" | "profesional"
    motivo_cancelacion = Column(Text)
    cancelado_en = Column(DateTime)
    
    creado_en = Column(DateTime, default=datetime.utcnow, index=True)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmado_en = Column(DateTime)
    finalizado_en = Column(DateTime)
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="turnos")
    profesional = relationship("Profesional", back_populates="turnos")
    servicio = relationship("Servicio", back_populates="turnos")
    
    # Constraints
    __table_args__ = (
        Index('ix_turno_prof_fecha_hora', 'profesional_id', 'fecha', 'hora_inicio'),
        Index('ix_turno_cliente_fecha', 'cliente_id', 'fecha'),
    )

class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    telefono = Column(String(20))
    fecha_nacimiento = Column(Date)
    preferencias = Column(JSON)  # futuro: notificaciones, etc.
    creado_en = Column(DateTime, default=datetime.utcnow)
    
    usuario = relationship("User", back_populates="cliente")
    turnos = relationship("Turno", back_populates="cliente")
```

## Endpoints API

### Cliente (rol CLIENTE - solo propios)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/turnos/disponibilidad` | Slots libres (query: profesional_id, servicio_id, desde, hasta) |
| POST | `/turnos` | Crear reserva manual |
| GET | `/turnos/mis-turnos` | Listar mis turnos (filtros: estado, fecha) |
| GET | `/turnos/{id}` | Detalle de mi turno |
| PUT | `/turnos/{id}/cancelar` | Cancelar mi turno (solo futuros, >2h) |

### Profesional (rol PROVEEDOR - solo suyos)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/profesionales/me/turnos` | Mi grilla de turnos (filtros: fecha, estado) |
| GET | `/profesionales/me/turnos/{id}` | Detalle turno |
| PUT | `/profesionales/me/turnos/{id}/estado` | Cambiar estado (CONFIRMADO→EN_CURSO→FINALIZADO) |
| PUT | `/profesionales/me/turnos/{id}/reasignar` | Mover a otro slot (body: nueva_fecha, nueva_hora) |
| PUT | `/profesionales/me/turnos/{id}/cancelar` | Cancelar con motivo |
| PUT | `/profesionales/me/turnos/{id}/notas` | Agregar/actualizar notas internas |

### Admin (rol ADMIN)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/admin/turnos` | Todos los turnos (filtros globales) |
| GET | `/admin/turnos/{id}` | Detalle cualquier turno |

### Interno (Chatbot Service)
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/internal/turnos/reservar` | Crear turno desde chatbot (api key interna) |

## Flujo de Estados

```
PENDIENTE → CONFIRMADO → EN_CURSO → FINALIZADO
                ↓
           CANCELADO_CLIENTE (cliente, >2h)
                ↓
           CANCELADO_PROVEEDOR (profesional, cualquier momento futuro)
                ↓
           NO_ASISTIO (profesional marca tras hora_fin + gracia)
```

## Reglas de Negocio

1. **Unicidad de slot**: Un profesional no puede tener 2 turnos solapados en mismo horario
2. **Duración**: `hora_fin = hora_inicio + servicio.duracion_min`
3. **Cancelación cliente**: Solo si `fecha_turno > now() + 2 horas` (configurable)
4. **Reasignación**: Solo a slots libres del MISMO profesional, mismo servicio
5. **Aislamiento**: Profesional solo ve SUS turnos (enforced by query filter)
6. **Historial inmutable**: Turnos FINALIZADO/CANCELADO no se modifican (solo notas)

## Criterios de Aceptación

1. Cliente ve slots libres de profesional para una semana
2. Cliente reserva → turno CONFIRMADO, slot ya no disponible
3. Profesional ve su grilla semanal con turnos coloreados
4. Profesional cambia estado: CONFIRMADO → EN_CURSO → FINALIZADO
4. Cliente cancela turno >2h antes → estado CANCELADO_CLIENTE, slot libre
5. Profesional cancela turno futuro → CANCELADO_PROVEEDOR, motivo requerido
6. Profesional reasigna turno a otro slot libre suyo
7. Historial cliente muestra solo sus turnos con estados correctos
8. Chatbot puede crear turno vía endpoint interno