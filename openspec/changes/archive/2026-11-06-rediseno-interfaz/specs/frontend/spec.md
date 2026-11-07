# Spec Delta: frontend (rediseño)

## ADDED Requirements

### Requirement: Tema claro y oscuro
La interfaz SHALL ofrecer tema claro, oscuro y "sistema", aplicado sin parpadeo al cargar y persistido entre visitas.

#### Scenario: Preferencia del sistema
- **WHEN** el usuario no eligió tema y su sistema está en modo oscuro
- **THEN** la app se muestra en tema oscuro

#### Scenario: Elección manual persistida
- **WHEN** el usuario elige "Claro" en el toggle y recarga la página
- **THEN** la app se muestra en tema claro

### Requirement: Navegación por rol
La interfaz SHALL mostrar una navegación lateral con solo las secciones del rol del usuario y SHALL reemplazarla por una barra inferior en pantallas menores a 768px.

#### Scenario: Cliente
- **WHEN** inicia sesión un CLIENTE
- **THEN** ve Inicio, Reservar y Mis turnos, no ve enlaces a rutas inexistentes, y tiene la burbuja del asistente abajo a la derecha

#### Scenario: Profesional
- **WHEN** inicia sesión un PROVEEDOR
- **THEN** llega a "Hoy" y ve Hoy, Agenda, Historial y Configuración

### Requirement: Landing pública
Un visitante sin sesión SHALL ver una landing en `/` con accesos a iniciar sesión y registrarse.

#### Scenario: Visitante
- **WHEN** un visitante sin sesión entra a `/`
- **THEN** ve la landing y no es redirigido al login

### Requirement: Reserva en pasos
El cliente SHALL reservar en cuatro pasos (profesional, servicio, fecha y hora, confirmación) con un resumen visible de lo elegido, y el paso actual SHALL quedar en la URL.

#### Scenario: Volver atrás
- **WHEN** el cliente está en el paso de fecha y hora y usa "atrás" del navegador
- **THEN** vuelve al paso de servicio con su elección anterior marcada

#### Scenario: Confirmación
- **WHEN** el cliente confirma en el paso 4 y el backend crea el turno
- **THEN** ve una pantalla de éxito con accesos a "Mis turnos" y "Reservar otro"

#### Scenario: Horario tomado mientras elegía
- **WHEN** el backend responde 409 al confirmar
- **THEN** el cliente vuelve al paso de fecha y hora con la disponibilidad recargada y un aviso

### Requirement: Agenda del día del profesional
El profesional SHALL tener una vista "Hoy" con sus turnos del día en orden cronológico y acciones de cambio de estado sobre cada turno.

#### Scenario: Iniciar atención
- **WHEN** el profesional pulsa "Iniciar atención" en un turno CONFIRMADO
- **THEN** el turno pasa a EN_CURSO y queda destacado en la lista
