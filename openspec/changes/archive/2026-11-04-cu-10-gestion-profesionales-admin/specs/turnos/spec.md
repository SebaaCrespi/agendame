# Spec Delta: turnos (CU-10)

## ADDED Requirements

### Requirement: Turnos de todos los profesionales para el administrador
La aplicación SHALL permitir al administrador consultar, en solo lectura, los turnos de todos los profesionales en una lista paginada, filtrable por profesional, estado y rango de fechas, mostrando fecha y hora, profesional, cliente, servicio y estado.

#### Scenario: Filtrar por profesional
- **WHEN** el admin elige a Juan Pérez en el filtro
- **THEN** ve solo los turnos de Juan, paginados

#### Scenario: Sin acciones
- **WHEN** el admin ve un turno confirmado
- **THEN** la lista no ofrece cancelar, reasignar ni cambiar el estado
