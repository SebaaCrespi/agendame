# Spec Delta: turnos (reserva sin cuenta)

## ADDED Requirements

### Requirement: Consulta de disponibilidad pública
La consulta de disponibilidad (`GET /turnos/disponibilidad`) SHALL responder sin sesión, para que un visitante elija horario antes de crear su cuenta (RF-TURNO-01, "Público/Cliente"). Un token inválido SHALL seguir respondiendo 401. Crear la reserva (`POST /turnos`) SHALL seguir requiriendo una cuenta de cliente.

#### Scenario: Visitante consulta horarios
- **WHEN** un visitante sin token consulta la disponibilidad de un profesional
- **THEN** el sistema responde 200 con los horarios

#### Scenario: Visitante intenta reservar
- **WHEN** un visitante sin token envía `POST /turnos`
- **THEN** el sistema responde 401 y no crea el turno


### Requirement: Retomar la reserva después de crear cuenta
El frontend SHALL permitir al visitante recorrer la reserva hasta el paso de confirmación y, al confirmar, SHALL pedirle crear una cuenta o iniciar sesión. Después SHALL llevarlo de vuelta al paso de confirmación con el profesional, servicio, fecha y horario que había elegido.

#### Scenario: Crear cuenta desde la reserva
- **WHEN** un visitante elige horario, pulsa "Crear cuenta y reservar" y crea su cuenta
- **THEN** vuelve al paso de confirmación con el turno elegido y lo confirma con un clic

#### Scenario: Ya tiene cuenta
- **WHEN** un visitante pulsa "Ya tengo cuenta" e inicia sesión
- **THEN** vuelve al paso de confirmación con el turno elegido

#### Scenario: Destino externo
- **WHEN** el parámetro `next` de login o registro apunta a otro sitio
- **THEN** se ignora y el usuario va a su panel
