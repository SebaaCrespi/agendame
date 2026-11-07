# Spec Delta: turnos (CU-07)

## ADDED Requirements

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
