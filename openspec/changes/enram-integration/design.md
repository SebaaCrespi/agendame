# Diseño: Integración Engram-OpenSpec

## Arquitectura de Integración

### Flujo de Trabajo Mejorado

1. **Sesión Start**: Al iniciar sesión OpenCode, ejecutar `mem_current_project` para detectar proyecto y contexto
2. **Decision Point**: Después de cualquier decisión arquitectónica o fix de bug, ejecutar `mem_save` automático
3. **Validation Point**: Antes de cierre de tarea, ejecutar `mem_doctor` para validar salud del store
4. **Context Recovery**: Al reanudar sesión, `mem_context` recupera observaciones recientes

### Ubicación de Artifacts

- `odd/tasks/<feature>.md`: Follow tracking per Organic Driven Development
- `odd/<feature-name>/tasks`: Engram mirror para recovery
- `.atl/skill-registry.md`: Skills registradas y versionadas
- `openspec/changes/<change-name>/`: Planning artifacts OpenSpec

### Patrón de `mem_save` Automatizado

```python
# Post-decision save pattern (to be integrated in workflow)
def after_decision(title, what, why, where, learned=""):
    mem_save({
        "title": title,
        "type": "decision" if "decision" in title.lower() else "bugfix",
        "scope": "project",
        "topic_key": infer_topic_key(what),
        "content": {
            "What": what,
            "Why": why,
            "Where": where,
            "Learned": learned
        }
    })
```

### Checklist `mem_doctor` en Pre-delivery

Executar antes de cada entrega/oarquive:
- `ambiguous_active_runtime_sessions`: Sin sessions ambiguas
- `invalid_session_identity`: Identity válida
- `manual_session_name_project_mismatch`: Sin mismatches
- `orphaned_observation_session`: Sin observaciones huérfanas
- `orphaned_pending_relations`: Sin relaciones pendientes
- `session_project_directory_mismatch`: Directorio coherente
- `sqlite_lock_contention`: WAL mode healthy, 0 contention
- `sync_mutation_required_fields`: Sin campos corruptos
- `sync_target_closed_space`: Espacio de sync saneado
- `unowned_session_project`: Sessions ownership OK

### Integración con Flujo OpenSpec

```
proposal.md  ←  design.md  ←  tasks.md
    │              │              │
    └─→ apply workflow ←─┘
    Con mem_save after cada decisión significativa
    Y mem_doctor validación pre-archive
```

### Skills OpenSpec Alineadas

Skills registradas en `.atl/skill-registry.md` que complementan la integración:
- `openspec-propose`: Nueva propuesta con artifacts
- `openspec-apply-change`: Implementar desde spec
- `openspec-explore`: Explorar antes de proponer
- `openspec-sync-specs`: Sincronizar delta specs
- `openspec-update-change`: Actualizar cambio existente
- `openspec-archive-change`: Archivar cambio completado