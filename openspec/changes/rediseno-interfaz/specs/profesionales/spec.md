# Spec Delta: profesionales (catálogo público)

## MODIFIED Requirements

### Requirement: Listado público de profesionales sin sesión
Los endpoints públicos de `/profesionales` (listado, detalle, servicios, grilla, excepciones y slots) SHALL responder sin sesión. Siguen devolviendo solo profesionales activos y sin datos de contacto privados.

#### Scenario: Visitante ve profesionales
- **WHEN** un visitante sin token pide `GET /profesionales`
- **THEN** el sistema responde 200 con los profesionales activos y sus servicios activos
