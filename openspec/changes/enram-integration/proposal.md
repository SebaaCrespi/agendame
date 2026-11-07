# Propuesta: Integración Engram-OpenSpec para Agendame

## Cambio
Integración de memoria persistente Engram con el flujo de trabajo Spec-Driven Development (OpenSpec) para el proyecto Agendame.

## Motivo (Why)
Actualmente el proyecto Agendame utiliza Engram para memoria persistente, pero el flujo de trabajo no está formalmente integrado con OpenSpec. Esto genera:
- Décisiones tomadas sin tracking estructurado en el ciclo de desarrollo
- Pérdida de contexto al cambiar de sesión o agente
- Dificultad para reproducir decisiones pasadas
- Falta de auditoría clara de cambios arquitectónicos

## Alcance
- Integrar `mem_save`, `mem_search`, `mem_context` y `mem_doctor` en el flujo OpenSpec
- Crear automatización para `mem_save` después de decisiones arquitectónicas y bugs
- Agregar verificación de estado Engram (`mem_doctor`) como check en el flujo
- Documentar skills OpenSpec alineadas a los casos de uso del proyecto
- Mantener compatibilidad con arquitectura Controllers → Services → Repositories

## Fuera de alcance
- Cambio de proveedor de memoria (seguir usando Engram)
- Reescritura de código existente que funcione
- Migración a otro sistema de memoria
- Modificaciones a la arquitectura del backend

## Beneficios esperados
1. **Persistencia de decisiones**: Cada decisión arquitectónica queda registrada y rastreable
2. **Recuperación de contexto**: Al iniciar nueva sesión, `mem_context` recupera estado relevante
3. **Validación de salud**: `mem_doctor` ejecuta checks automáticos antes de entregas
4. **Tracing completo**: Desde decisión hasta implementación, traceable via Engram IDs
5. **Alinhamento OpenSpec**: Skills y workflows formalmente definidos y versionados

## Dépendencias
- Proyecto Agendame con estructura OpenSpec existente (`openspec/specs/`)
- Engram operativo (verificado: 10/10 checks OK en `mem_doctor`)
- Skills OpenSpec registradas en `.atl/skill-registry.md`

## Aceptación
- [ ] proposal.md creado y revisado
- [ ] design.md creado con arquitectura de integración
- [ ] tasks.md creado con pasos de implementación
- [ ] specs delta creadas para dominios afectados
- [ ] mem_save prototype validado en sesión de test
- [ ] mem_doctor check integrado en pre-check CI