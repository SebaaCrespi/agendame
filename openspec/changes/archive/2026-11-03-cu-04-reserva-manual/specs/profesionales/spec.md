# Spec Delta: profesionales (listado público para CU-04)

## ADDED Requirements

### Requirement: Listado público de profesionales con servicios
El listado público de profesionales SHALL devolver una lista paginada con solo los profesionales activos. Cada profesional SHALL incluir id, nombre, apellido, bio, foto, duración de slot y sus servicios activos (id, nombre, descripción, duración en minutos y precio en centavos).

#### Scenario: Listado con servicios
- **WHEN** un cliente autenticado consulta el listado y hay un profesional activo con dos servicios activos y uno inactivo
- **THEN** la respuesta incluye a ese profesional con sus dos servicios activos

#### Scenario: Profesional inactivo
- **WHEN** existe un profesional inactivo
- **THEN** no aparece en el listado público

### Requirement: Listado público sin datos privados
El listado público y el detalle público de un profesional SHALL NOT exponer su email ni el id de su usuario.

#### Scenario: Sin email
- **WHEN** un cliente consulta el listado público
- **THEN** ningún profesional de la respuesta tiene los campos email ni user_id
