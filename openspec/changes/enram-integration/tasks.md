# Tareas: Integración Engram-OpenSpec

## Tarea T1: Configurar tracking `mem_save` post-decision
- **S#**: S1 - Definir patrón de guardado automático
- **Route**: inline (small task)
- **Status**: pending
- **Comandos**:
  1. Probar `mem_save` manual después de una decisión en sesión de test
  2. Validar que observation se guarda en Engram con `mem_search`
  3. Verificar `mem_get_observation` recupera el contenido

## Tarea T2: Integrar `mem_doctor` en validación pre-entrega
- **S#**: S2 - Agregar check de salud Engram
- **Route**: inline (small task)
- **Status**: pending
- **Comandos**:
  1. Ejecutar `mem_doctor {}` y verificar 10/10 checks OK
  2. Documentar resultado esperado en `design.md`
  3. Integrar como paso automatizado en flujo

## Tarea T3: Crear recuperación de contexto `mem_context` en sesión start
- **S#**: S3 - Recovery pattern design
- **Route**: inline (small task)
- **Status**: pending
- **Comandos**:
  1. Probar `mem_context {project: "agendame"}` al iniciar nueva sesión
  2. Verificar retornos recientes de decisiones y observaciones
  3. Documentar patrón de re-utilización

## Tarea T4: Alinear skills OpenSpec al casos de uso
- **S#**: S4 - Skills mapping
- **Route**: inline (small task)
- **Status**: pending
- **Comandos**:
  1. Revisar `.atl/skill-registry.md` tiene 7 skills listadas
  2. Validar que triggers coinciden con flujo ODD
  3. Documentar mapping en `design.md`

## Tarea T5: Validar integración end-to-end
- **S#**: S5 - End-to-end test
- **Route**: inline (small task)
- **Status**: pending
- **Comandos**:
  1. Flujo completo: proposal → design → tasks → apply → archive
  2. Verificar `mem_save` persiste decisiones clave
  3. Verificar `mem_doctor` valida estado después
  4. Generar `mem_session_summary` al cerrar

## Dependencias entre tareas
- T1 debe completarse antes que T2 (patrón que usa mem_save)
- T3 depende de T1 (contexto usa patrón de save)
- T4 es independiente pero complementa la integración
- T5 valida todo el conjunto

## Definición de Done
- [ ] Las 5 tareas S1-S5 completadas
- [ ] `mem_save` funciona y persiste decisiones
- [ ] `mem_doctor` retorna 10/10 checks OK
- [ ] `mem_context` recupera estado relevante
- [ ] Skills OpenSpec mapeadas y documentadas
- [ ] Flujo end-to-end probado y documentado