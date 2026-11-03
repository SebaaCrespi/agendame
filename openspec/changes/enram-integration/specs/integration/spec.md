# Spec Delta: Integración Engram-OpenSpec (CU-0X: Memoria Persistente y Flujo de Trabajo)

## Resumen
Integración de memoria persistente Engram con el flujo de trabajo Spec-Driven Development (OpenSpec) para el proyecto Agendame. Esta spec define los requisitos funcionales y no funcionales para la integración, sin modificar las specs dominio existentes (auth, profesionales, turnos, chatbot).

## Alcance de la Integración
- Persistencia de decisiones arquitectónicas via `mem_save`
- Recuperación de contexto de sesión via `mem_context`
- Validación de salud del store via `mem_doctor`
- Tracing de decisiones a implementación
- Alineación de skills OpenSpec con casos de uso

## Requisitos Funcionales

### RF-EGR-01: Guardado automático de decisiones
- **Descripción**: Después de tomar una decisión arquitectónica o fix de bug, el sistema debe guardar la decisión en Engram automáticamente
- **Entrada**: Título, tipo, scope, topic_key, content (What/Why/Where/Learned)
- **Salida**: Observation ID generado en Engram, verificación de guardado exitosa
- **Validaciones**: 
  - Decision guardada con `mem_save` exitoso
  - Observation ID retornado y válido
  - `mem_search` encuentra la observation por topic_key

### RF-EGR-02: Recuperación de contexto de sesión
- **Descripción**: Al iniciar nueva sesión, recuperar contexto relevante previo
- **Entrada**: project name (ej. "agendame")
- **Salida**: Observaciones recientes, decisiones clave, skills mapeadas
- **Validaciones**:
  - `mem_context` retorna historial de sesión
  - `mem_search` encuentra observaciones por keywords
  - Session ID coherente across compactions

### RF-EGR-03: Validación de salud Engram pre-entrega
- **Descripción**: Ejecutar checks de salud antes de archivar cambios
- **Entrada**: Ninguna (ejecución autónoma)
- **Salida**: Reporte de 10/10 checks OK o lista de problemas
- **Validaciones**:
  - `mem_doctor {}` retorna status "ok"
  - Summary: total checks, ok count, warnings, errors
  - Cada check_id evaluado y resultado registrado

### RF-EGR-04: Mapeo de skills OpenSpec
- **Descripción**: Skills registradas deben alinearse a flujo ODD y casos de uso
- **Entrada**: `.atl/skill-registry.md`
- **Salida**: Lista de 7 skills con triggers, scopes y paths validados
- **Validaciones**:
  - Cada skill tiene trigger/description definido
  - Scope es "project" para todas
  - Path apunta a archivo SKILL.md existente
  - Total: 6 skills de OpenSpec + proyecto

### RF-EGR-05: Integración con flujo Organic Driven Development (ODD)
- **Descripción**: El flujo ODD debe considerar Engram como layer de memoria persistente
- **Entrada**: Request de trabajo, decisión tomada, implementación
- **Salida**: Tracking completo via `odd/tasks/<feature>.md` y mirror en `odd/<feature-name>/tasks`
- **Validaciones**:
  - Cada decisión grande tiene `mem_save` asociado
  - Cada tarea completada tiene evidence en Engram
  - `mem_session_summary` llamado al cerrar sesión

## Requisitos No Funcionales

### RNF-EGR-01: Performance
- `mem_save` debe completarse en < 200ms
- `mem_doctor` completa 10 checks en < 2s
- `mem_context` retorna en < 500ms

### RNF-EGR-02: Reliability
- `mem_save` debe ser atómico: o se guarda completo o no se guarda
- `mem_doctor` debe ser determinista en mismo estado
- Fallos gracefull: si Engram está unavailable, workflow continúa con warning

### RNF-EGR-03: Consistency
- Engram state debe ser coherente con `odd/tasks/` document
- `mem_session_summary` debe reflejar accomplishments exactas
- Topic keys must not overwrite different topics (upsert semantics)

## Criterios de Aceptación

1. [ ] Después de cualquier decisión arquitectónica, `mem_save` perserva la observation
2. [ ] `mem_doctor {}` siempre retorna 10/10 checks OK en estado base
3. [ ] `mem_context {project: "agendame"}` retorna historial no vacío después de sesión con decisiones
4. [ ] Skills OpenSpec (6 skills) tienen triggers definidos y paths a SKILL.md existentes
5. [ ] Flujo ODD: propuesta → design → tasks → apply → archive con mem_save en puntos clave
6. [ ] `mem_session_summary` se ejecuta automáticamente al cerrar sesión
7. [ ] Topic keys usan upsert semantics (mismo topic_key actualiza, no sobrescribe diferente)
8. [ ] Integración no rompe flujo existente: auth, profesionales, turnos, chatbot sin cambios

## Relación con Casos de Uso del Proyecto

| CU | Impacto | Tipo de Integración |
|----|---------|---------------------|
| CU-01 | Alto | Session auth + decision tracking |
| CU-02 | Alto | Professional decisions tracking |
| CU-03 | Medio | Turno flow decision points |
| CU-04 | Bajo | Reservation edge cases |
| CU-05 | Bajo | Chatbot decision logging |
| CU-06 | Medio | Integration points |
| CU-07 | Bajo | Error handling |
| CU-08 | Bajo | State transitions |
| CU-09 | Bajo | Cancellation flow |
| CU-10 | Alto | Professional RBAC decisions |

## Fuera de alcance (Explicit)
- Modificación de specs dominio existentes (auth/spec.md, profesionales/spec.md, etc.)
- Cambio de proveedor de memoria (continuar usando Engram)
- Reescritura de código backend que funcione
- Migración a sistema de memoria alternativo