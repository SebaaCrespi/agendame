# Spec Delta: profesionales (CU-10)

## ADDED Requirements

### Requirement: Baja de profesional con turnos pendientes
El sistema SHALL rechazar con 409 la desactivación de un profesional que tenga turnos PENDIENTE, CONFIRMADO o EN_CURSO cuya hora de fin todavía no llegó según la hora del negocio, tanto por `DELETE /admin/profesionales/{id}` como por `PUT /admin/profesionales/{id}` con `activo: false`. La respuesta SHALL indicar cuántos turnos lo impiden. Reactivar un profesional SHALL estar siempre permitido.

#### Scenario: Baja por edición con turnos
- **WHEN** el admin envía `activo: false` para un profesional con un turno CONFIRMADO mañana
- **THEN** el sistema responde 409 y el profesional sigue activo

#### Scenario: Baja con turnos ya terminados
- **WHEN** el profesional solo tiene turnos CONFIRMADO que terminaron hoy más temprano
- **THEN** la desactivación se acepta

#### Scenario: Reactivar
- **WHEN** el admin envía `activo: true` para un profesional inactivo
- **THEN** el profesional vuelve a figurar en el listado público

### Requirement: Gestión de profesionales desde la interfaz
La aplicación SHALL permitir al administrador listar los profesionales (paginado, con búsqueda por nombre y filtro por activos o inactivos), crear uno con su usuario PROVEEDOR, editar sus datos, desactivarlo y reactivarlo. Los errores del sistema (email ya registrado, turnos que impiden la baja) SHALL mostrarse en la pantalla.

#### Scenario: Alta de profesional
- **WHEN** el admin crea a "Lucía Díaz" con email y contraseña temporal
- **THEN** Lucía aparece activa en la lista y puede iniciar sesión como proveedor

#### Scenario: Email repetido
- **WHEN** el admin crea un profesional con un email ya registrado
- **THEN** la pantalla muestra el error y no crea nada

#### Scenario: Baja impedida
- **WHEN** el admin desactiva a un profesional con turnos pendientes
- **THEN** la pantalla muestra cuántos turnos lo impiden y el profesional sigue activo

#### Scenario: Grillas independientes
- **WHEN** el admin crea un profesional nuevo
- **THEN** el profesional empieza sin servicios ni grilla y no ve los de otros profesionales
