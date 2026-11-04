# Spec Delta: turnos (CU-08)

## ADDED Requirements

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
