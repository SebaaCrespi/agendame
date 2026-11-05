# Tasks: CU-02 Configuración del proveedor

## 1. Protección de turnos activos (backend)

- [x] 1.1 Agregar `TurnoRepo.get_activos_futuros(profesional_id)` y el helper `_turnos_fuera_de_horario` en `DisponibilidadService`. Verificar: tests unitarios del helper (turno dentro, empieza antes, termina después, día sin atención)
- [x] 1.2 Validar en `actualizar_grilla_completa` (respetando excepciones existentes) y en `agregar_excepcion` (CERRADO y HORARIO_ESPECIAL), lanzando `ConflictException` con la cantidad y hasta 5 fechas. Verificar: tests de API para los escenarios del spec (acortar con y sin turnos, quitar un día, cancelados/pasados no bloquean, cerrar día con turnos, horario especial compatible)

## 2. Páginas del proveedor

- [x] 2.1 Crear `pages/profesional/PerfilPage.tsx` y su ruta. Verificar: `npm run build`
- [x] 2.2 Crear `pages/profesional/ServiciosPage.tsx` (lista, alta/edición en `Dialog`, desactivar con confirmación, precio en pesos) y su ruta. Verificar: `npm run build`
- [x] 2.3 Crear `pages/profesional/DisponibilidadPage.tsx` (grilla semanal y excepciones) y su ruta. Verificar: `npm run build` y `npm run lint` sin errores

## 3. Verificación end-to-end

- [x] 3.1 En el navegador, como Juan: editar el perfil; crear, editar y desactivar un servicio (y ver el error de nombre repetido); cambiar la semana y ver los slots en la reserva del cliente; intentar cerrar un día con turnos y ver el 409; agregar y eliminar una excepción. Revisar las tres páginas a 375 px. Verificar: capturas
- [x] 3.2 Suite completa en verde y `ruff check app/` limpio. Verificar: `pytest` y `ruff check app/`

## Workflow follow-up

- `/opsx-archive` del change una vez implementado y revisado
- `mem_save` en Engram con las decisiones (validación de turnos huérfanos)
