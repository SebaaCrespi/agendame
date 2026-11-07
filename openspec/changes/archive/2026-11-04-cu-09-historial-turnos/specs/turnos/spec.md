# Spec Delta: turnos (CU-09)

## ADDED Requirements

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
