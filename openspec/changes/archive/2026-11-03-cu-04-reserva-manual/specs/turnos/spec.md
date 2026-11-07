# Spec Delta: turnos (CU-04)

## ADDED Requirements

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
