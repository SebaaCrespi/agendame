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

### Requirement: Reasignación a un slot válido
El proveedor SHALL poder mover un turno PENDIENTE o CONFIRMADO propio a otro horario solo si ese horario es un slot disponible suyo para la duración del servicio del turno, con las mismas reglas de la reserva (grilla, excepciones, cierre, alineación, pasado). El propio turno no cuenta como ocupado. Fuera de horario, desalineado o pasado → 422; ocupado por otro turno → 409.

#### Scenario: Reasignación a un slot libre
- **WHEN** el proveedor mueve un turno de las 10:00 a las 15:00 de otro día con horario de atención
- **THEN** el turno queda de 15:00 a 15:00 + duración del servicio y el horario de las 10:00 queda libre

#### Scenario: Reasignación fuera de horario
- **WHEN** el proveedor mueve un turno a las 03:00
- **THEN** el sistema responde 422 y el turno no cambia

#### Scenario: Reasignación a un día cerrado
- **WHEN** el proveedor mueve un turno a una fecha con excepción CERRADO
- **THEN** el sistema responde 422

#### Scenario: Reasignación a un horario ocupado
- **WHEN** el proveedor mueve un turno a un horario que se solapa con otro turno activo
- **THEN** el sistema responde 409

#### Scenario: Corrimiento sobre el propio horario
- **WHEN** el proveedor mueve un turno de 60 min de las 10:00 a las 10:30 y no hay otros turnos
- **THEN** el sistema acepta la reasignación

### Requirement: Auditoría de reasignación
Al reasignar, el sistema SHALL guardar en el turno el inicio anterior, el motivo y el momento de la reasignación, y SHALL devolverlos en las respuestas del turno. Si el turno se reasigna otra vez, se conserva solo el último registro.

#### Scenario: Registro de la reasignación
- **WHEN** el proveedor reasigna un turno de las 10:00 a las 15:00 con motivo "Enfermedad"
- **THEN** la respuesta incluye reasignado_desde con las 10:00, motivo_reasignacion "Enfermedad" y reasignado_en

### Requirement: Cancelación del proveedor por fuerza mayor
El proveedor SHALL poder cancelar, con motivo obligatorio, un turno propio PENDIENTE o CONFIRMADO que todavía no empezó, o un turno EN_CURSO. Un turno PENDIENTE o CONFIRMADO cuya hora de inicio ya pasó SHALL rechazarse con 422. El slot queda libre de inmediato.

#### Scenario: Cancelar un turno futuro
- **WHEN** el proveedor cancela un turno CONFIRMADO de mañana con motivo "Corte de luz"
- **THEN** el turno queda CANCELADO_PROFESIONAL con ese motivo y el horario vuelve a estar disponible

#### Scenario: Cancelar un turno que ya pasó
- **WHEN** el proveedor intenta cancelar un turno CONFIRMADO cuya hora de inicio ya pasó
- **THEN** el sistema responde 422

#### Scenario: Cancelar un turno en curso
- **WHEN** el proveedor cancela un turno EN_CURSO
- **THEN** el turno queda CANCELADO_PROFESIONAL

### Requirement: Disponibilidad para el proveedor
El proveedor SHALL poder consultar sus propios slots en un rango de fechas (máximo 60 días), opcionalmente con la duración de uno de sus servicios y excluyendo un turno propio de los ocupados.

#### Scenario: Slots excluyendo el turno a reasignar
- **WHEN** el proveedor consulta sus slots del día de un turno de las 10:00 excluyendo ese turno
- **THEN** el slot de las 10:00 figura disponible

#### Scenario: Servicio ajeno
- **WHEN** el proveedor consulta con un servicio que no es suyo
- **THEN** el sistema responde 404

### Requirement: Cancelación y reasignación desde la interfaz
La aplicación SHALL permitir al cliente cancelar desde "Mis turnos" con un diálogo que pide motivo, solo en los turnos cancelables. También SHALL permitir al proveedor cancelar o reasignar desde el detalle del turno, eligiendo fecha y uno de los slots libres que devuelve el sistema. Los errores del backend SHALL mostrarse en el diálogo.

#### Scenario: Cliente cancela
- **WHEN** el cliente cancela un turno de pasado mañana ingresando un motivo
- **THEN** el turno aparece como cancelado en "Mis turnos"

#### Scenario: Proveedor reasigna
- **WHEN** el proveedor elige "Reasignar", selecciona otra fecha y un slot libre, e ingresa un motivo
- **THEN** el turno aparece en el nuevo horario de la grilla

### Requirement: Historial por momento
Los listados de turnos del cliente y del proveedor SHALL aceptar un filtro opcional `momento` (`proximos` o `pasados`) según la hora del negocio: un turno es pasado cuando ya llegó su hora de fin. Los próximos SHALL ordenarse del más cercano al más lejano y los pasados del más reciente al más viejo. Sin `momento` se conserva el orden actual de cada rol.

#### Scenario: Próximos del cliente
- **WHEN** el cliente tiene turnos ayer, hoy más tarde y mañana, y pide `momento=proximos`
- **THEN** recibe los de hoy y mañana, en ese orden

#### Scenario: Pasados del proveedor
- **WHEN** el proveedor tiene turnos hace 3 días, ayer y mañana, y pide `momento=pasados`
- **THEN** recibe el de ayer y después el de hace 3 días

#### Scenario: Turno en curso
- **WHEN** un turno empezó hace 10 minutos y termina en 20, y se pide `momento=proximos`
- **THEN** el turno figura en la respuesta

#### Scenario: Momento inválido
- **WHEN** se pide `momento=ayer`
- **THEN** el sistema responde 422

### Requirement: Filtro por varios estados
Los listados de turnos del cliente y del proveedor SHALL aceptar el parámetro `estado` repetido para filtrar por cualquiera de los estados indicados. Un solo valor SHALL seguir filtrando por ese estado. Un estado inexistente SHALL responder 422. El total y la paginación SHALL corresponder al conjunto filtrado.

#### Scenario: Cancelados por cualquiera de las partes
- **WHEN** el cliente pide `estado=CANCELADO_CLIENTE&estado=CANCELADO_PROFESIONAL`
- **THEN** recibe todos sus turnos cancelados y ningún otro, y el total cuenta solo esos

#### Scenario: Estado inexistente
- **WHEN** se pide `estado=BORRADO`
- **THEN** el sistema responde 422

### Requirement: Historial del cliente en la interfaz
La sección "Mis turnos" del cliente SHALL separar Próximos y Pasados, SHALL permitir filtrar por grupo de estado (Todos, Activos, Finalizados, Cancelados, No asistió) y por rango de fechas, y SHALL mostrar en cada turno la fecha y hora, el profesional, el servicio y el estado en texto legible. Los turnos cancelados SHALL mostrar el motivo y los reasignados el horario anterior. Cambiar de página SHALL mostrar los turnos de la página elegida.

#### Scenario: Turnos cancelados
- **WHEN** el cliente abre Pasados y elige el grupo Cancelados
- **THEN** ve solo sus turnos cancelados, cada uno con su motivo

#### Scenario: Datos del turno
- **WHEN** el cliente ve un turno de Corte con Juan Pérez
- **THEN** la fila muestra "Juan Pérez" y "Corte"

#### Scenario: Paginación
- **WHEN** el cliente tiene 25 turnos pasados y pasa a la página 2
- **THEN** ve los turnos 11 a 20

### Requirement: Historial del proveedor en la interfaz
El proveedor SHALL tener una página de historial con sus turnos paginados, filtrable por momento, estado, rango de fechas, servicio y cliente, que abre el detalle del turno al seleccionarlo. Los turnos pasados que siguen PENDIENTE o CONFIRMADO SHALL señalarse como "Sin cerrar".

#### Scenario: Turnos sin cerrar
- **WHEN** el proveedor abre el historial de pasados y tiene un turno de ayer CONFIRMADO
- **THEN** el turno aparece marcado "Sin cerrar" y desde el detalle puede marcarlo ausente

#### Scenario: Historial de varias semanas
- **WHEN** el proveedor filtra del 1 al 31 del mes con el servicio Corte
- **THEN** ve solo los turnos de Corte de ese mes, paginados

### Requirement: Turnos de todos los profesionales para el administrador
La aplicación SHALL permitir al administrador consultar, en solo lectura, los turnos de todos los profesionales en una lista paginada, filtrable por profesional, estado y rango de fechas, mostrando fecha y hora, profesional, cliente, servicio y estado.

#### Scenario: Filtrar por profesional
- **WHEN** el admin elige a Juan Pérez en el filtro
- **THEN** ve solo los turnos de Juan, paginados

#### Scenario: Sin acciones
- **WHEN** el admin ve un turno confirmado
- **THEN** la lista no ofrece cancelar, reasignar ni cambiar el estado
