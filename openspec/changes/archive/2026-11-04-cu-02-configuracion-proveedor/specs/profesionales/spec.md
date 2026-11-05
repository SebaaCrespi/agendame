# Spec Delta: profesionales (CU-02)

## ADDED Requirements

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
