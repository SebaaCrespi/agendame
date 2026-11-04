# Especificación de Dominio: Turnos y Reservas (CU-04, CU-07, CU-08, CU-09)

## Purpose

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

## Requirements

<!-- Agregados por el change cu-04-reserva-manual (CU-04) -->

### Requirement: Reserva dentro del horario de atención
El sistema SHALL rechazar con 422 una reserva cuyo intervalo completo (hora de inicio + duración del servicio) no caiga dentro del horario efectivo del profesional para ese día. El horario efectivo es el de su grilla semanal, salvo que haya una excepción para la fecha: CERRADO anula el día y HORARIO_ESPECIAL reemplaza el horario.

#### Scenario: Reserva dentro del horario
- **WHEN** el profesional atiende de 09:00 a 18:00 ese día y el cliente reserva un servicio de 30 min a las 10:00
- **THEN** el sistema crea el turno CONFIRMADO de 10:00 a 10:30

#### Scenario: Reserva fuera del horario
- **WHEN** el profesional atiende de 09:00 a 18:00 y el cliente reserva a las 07:00
- **THEN** el sistema responde 422 y no crea el turno

#### Scenario: El servicio no entra antes del cierre
- **WHEN** el profesional cierra a las 18:00 y el cliente reserva un servicio de 60 min a las 17:30
- **THEN** el sistema responde 422

#### Scenario: Día sin atención en la grilla
- **WHEN** el profesional no tiene grilla para ese día de la semana
- **THEN** el sistema responde 422

#### Scenario: Día cerrado por excepción
- **WHEN** existe una excepción CERRADO para la fecha pedida
- **THEN** el sistema responde 422

#### Scenario: Horario especial por excepción
- **WHEN** existe una excepción HORARIO_ESPECIAL de 10:00 a 14:00 y el cliente reserva a las 15:00
- **THEN** el sistema responde 422

### Requirement: Reserva alineada a la grilla de slots
El sistema SHALL rechazar con 422 una reserva cuya hora de inicio no coincida con el inicio de un slot del profesional, es decir, con el comienzo del horario efectivo más un múltiplo de su duración de slot.

#### Scenario: Inicio desalineado
- **WHEN** los slots del profesional son de 30 min desde las 09:00 y el cliente reserva a las 09:10
- **THEN** el sistema responde 422

### Requirement: Disponibilidad según la duración del servicio
Cuando la consulta de disponibilidad incluye un servicio, el sistema SHALL marcar un slot como disponible solo si el servicio completo, empezando en ese slot, termina dentro del horario efectivo y no se solapa con turnos activos.

#### Scenario: Servicio largo antes de un turno ocupado
- **WHEN** hay un turno de 10:00 a 10:30 y se consulta un servicio de 60 min
- **THEN** el slot de las 09:30 figura como no disponible y el de las 09:00 como disponible

#### Scenario: Servicio largo al cierre
- **WHEN** el profesional cierra a las 18:00 y se consulta un servicio de 60 min
- **THEN** el slot de las 17:30 figura como no disponible

#### Scenario: Consulta sin servicio
- **WHEN** la consulta no incluye servicio
- **THEN** cada slot se evalúa con la duración de slot del profesional

### Requirement: Horarios pasados no disponibles
El sistema SHALL marcar como no disponibles los slots cuyo inicio ya pasó según la hora actual del negocio, y SHALL rechazar con 422 la reserva de un horario pasado.

#### Scenario: Slots de hoy que ya pasaron
- **WHEN** son las 12:00 hora del negocio y se consulta la disponibilidad de hoy
- **THEN** los slots que empiezan antes de las 12:00 figuran como no disponibles

#### Scenario: Reserva en el pasado
- **WHEN** el cliente reserva un horario anterior a la hora actual del negocio
- **THEN** el sistema responde 422

### Requirement: Hora del negocio
El sistema SHALL interpretar las fechas y horas de turnos, grillas y excepciones como hora local del negocio, en una zona horaria configurable (por defecto America/Argentina/Buenos_Aires), y SHALL usar esa zona para calcular "ahora" en todas las reglas que dependen del momento actual, incluida la cancelación con más de 2 h de antelación.

#### Scenario: Validación de pasado con hora local
- **WHEN** son las 21:00 en Buenos Aires (00:00 UTC del día siguiente) y el cliente reserva hoy a las 21:30
- **THEN** el sistema acepta la reserva

#### Scenario: Cancelación con hora local
- **WHEN** son las 20:00 en Buenos Aires y el cliente cancela un turno de hoy a las 23:00
- **THEN** el sistema acepta la cancelación (faltan más de 2 h)

<!-- Agregados por el change cu-07-gestion-grilla-proveedor (CU-07) -->

### Requirement: Datos legibles del turno
Toda respuesta que devuelva un turno SHALL incluir, además de los ids, el nombre del cliente, su teléfono (si lo tiene), el nombre del servicio y el nombre completo del profesional.

#### Scenario: Turno en el listado del proveedor
- **WHEN** el proveedor lista sus turnos y uno es del cliente "Ana" por el servicio "Corte"
- **THEN** ese turno incluye cliente_nombre "Ana" y servicio_nombre "Corte"

#### Scenario: Turno en el listado del cliente
- **WHEN** el cliente lista sus turnos
- **THEN** cada turno incluye servicio_nombre y profesional_nombre

### Requirement: Filtros del listado del proveedor
El listado de turnos del proveedor SHALL aceptar, combinables entre sí, filtros por estado, rango de fechas, servicio (id) y cliente (texto contenido en el nombre, sin distinguir mayúsculas). Siempre SHALL devolver solo turnos del propio proveedor, ordenados por fecha de inicio ascendente.

#### Scenario: Filtro por servicio
- **WHEN** el proveedor tiene turnos de "Corte" y de "Color" y filtra por el servicio "Color"
- **THEN** solo recibe los turnos de "Color"

#### Scenario: Filtro por cliente
- **WHEN** el proveedor filtra por cliente "ana"
- **THEN** recibe los turnos de "Ana López" y no los de "Beto"

#### Scenario: Filtros combinados
- **WHEN** el proveedor filtra por estado CONFIRMADO y por una semana
- **THEN** recibe solo los turnos confirmados de esa semana

#### Scenario: Servicio de otro profesional
- **WHEN** el proveedor filtra por un servicio que no es suyo
- **THEN** recibe una lista vacía

### Requirement: Marcar ausencia
El proveedor SHALL poder pasar un turno de CONFIRMADO a NO_ASISTIO solo si la hora de inicio del turno ya pasó según la hora del negocio. Antes de esa hora, la transición SHALL rechazarse con 422.

#### Scenario: Ausencia después de la hora
- **WHEN** un turno CONFIRMADO empezaba a las 10:00 y son las 10:20
- **THEN** el proveedor puede marcarlo NO_ASISTIO

#### Scenario: Ausencia antes de la hora
- **WHEN** un turno CONFIRMADO empieza a las 10:00 y son las 09:00
- **THEN** marcarlo NO_ASISTIO responde 422 y el estado no cambia

### Requirement: Grilla semanal del proveedor
La aplicación SHALL mostrar al proveedor sus turnos de una semana (lunes a domingo) con navegación entre semanas, cada turno coloreado según su estado y con hora, cliente y servicio. Al seleccionar un turno SHALL mostrar su detalle y ofrecer solo los cambios de estado válidos desde su estado actual y la edición de las notas internas.

#### Scenario: Ver la semana
- **WHEN** el proveedor abre "Mis turnos"
- **THEN** ve la semana actual con sus turnos ubicados por día y hora

#### Scenario: Acciones válidas
- **WHEN** el proveedor selecciona un turno CONFIRMADO
- **THEN** se le ofrece pasarlo a EN_CURSO, y a NO_ASISTIO solo si ya pasó su hora de inicio

#### Scenario: Turno finalizado
- **WHEN** el proveedor selecciona un turno FINALIZADO
- **THEN** no se ofrece ningún cambio de estado, pero puede editar las notas

### Requirement: Inicio según el rol
Al entrar a la aplicación autenticado, el usuario SHALL ser llevado al panel de su rol: CLIENTE a su panel de reservas, PROVEEDOR a su panel de turnos y ADMIN a su panel de administración.

#### Scenario: Proveedor inicia sesión
- **WHEN** un PROVEEDOR inicia sesión
- **THEN** llega a su panel sin redirecciones en loop
