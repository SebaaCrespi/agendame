# Design: CU-02 Configuración del proveedor

## Context

El motivo está en proposal.md y el comportamiento en `specs/profesionales`. Estado actual:

- `DisponibilidadService.actualizar_grilla_completa` reemplaza la grilla (una entrada por día, sin duplicados) y `agregar_excepcion` solo rechaza una segunda excepción para la misma fecha. Ninguno mira los turnos.
- `SlotRepo._generate_slots` ya resuelve qué horario rige cada fecha (grilla del día, o excepción CERRADO / HORARIO_ESPECIAL).
- Las fechas de turno son hora del negocio; "ahora" es `ahora_negocio()`.
- El frontend ya tiene en `api.ts` todos los métodos (`getMiPerfil`, `updateMiPerfil`, `getMisServicios`, `crearServicio`, `actualizarServicio`, `desactivarServicio`, `getMiGrilla`, `actualizarGrillaCompleta`, `getMisExcepciones`, `agregarExcepcion`, `eliminarExcepcion`) y los componentes `Input`, `Textarea`, `Button`, `Card` y `Dialog`.

## Goals / Non-Goals

**Goals:**
- Una sola función que decida si un turno entra en el horario que regiría su fecha, usada por la grilla y por las excepciones.

**Non-Goals:**
- Cambiar la forma de los endpoints o el modelo.
- Una librería de formularios.

## Decisions

### 1. Validación de turnos afectados en el servicio
`DisponibilidadService` obtiene los turnos activos futuros del profesional (`fecha_fin > ahora_negocio()`, estados PENDIENTE, CONFIRMADO, EN_CURSO) con un método nuevo `TurnoRepo.get_activos_futuros(profesional_id)`. Para cada turno calcula el horario que regiría su fecha con la configuración propuesta y verifica `inicio >= hora_inicio` y `fin <= hora_fin` del día:
- **Grilla nueva**: excepción existente de esa fecha si la hay; si no, la entrada de la grilla nueva para ese día de semana (sin entrada o inactiva = no atiende).
- **Excepción nueva**: solo los turnos de esa fecha, contra la excepción (CERRADO = no atiende).

Los turnos afectados se informan con `ConflictException` (409) y un `detail` legible: "N turnos quedarían fuera de horario: 24/11 15:00, …" (hasta 5 fechas). La regla vive en un helper puro `_turnos_fuera_de_horario(turnos, horario_por_fecha)` fácil de testear.
- *Alternativa*: permitir el cambio y avisar. Se descarta porque los turnos quedarían visibles para el cliente fuera de la atención y la reasignación (CU-08) los rechazaría.
- *Alternativa*: reutilizar `SlotRepo` generando slots. Se descarta: alinea a la grilla de slots y un turno válido podría no coincidir con un inicio de slot si cambió la duración base.

### 2. Endpoints
Hoy `PUT /disponibilidad` traduce `ValueError` a 400 y `POST /excepciones` a 409. La validación nueva lanza `ConflictException`, que el manejador global ya convierte en 409 con `detail`, sin tocar el controller.

### 3. Páginas del frontend
- **PerfilPage**: formulario con los campos de `ProfesionalUpdate`; muestra el email en solo lectura. Guardar envía solo lo que cambió.
- **ServiciosPage**: lista en tarjetas; "Nuevo servicio" y "Editar" abren un `Dialog` con el formulario; "Desactivar" pide confirmación en un `Dialog`. El precio se edita en pesos y se convierte a centavos al enviar.
- **DisponibilidadPage**: dos secciones. Grilla: 7 filas (lunes a domingo) con casilla "Atiende" e inputs `time`; "Guardar semana" envía solo los días marcados. Excepciones: lista de las próximas (desde hoy) y un formulario de alta (fecha, tipo, horario si es especial, motivo) con botón eliminar por fila.
- Cada página tiene su estado de error/éxito; los mensajes del backend (incluido el 409 con turnos) se muestran tal cual.

## Risks / Trade-offs

- [Proveedor con muchos turnos futuros] → La consulta trae todos los activos futuros del profesional; para el TP el volumen es chico. Se puede acotar por fecha si crece.
- [Un turno que hoy ya está fuera de horario bloquea cualquier cambio de grilla] → El 409 lo lista; el proveedor lo reasigna o cancela. Es preferible a ocultarlo.
- [Excepción eliminada que dejaba fuera turnos] → Eliminar una excepción vuelve a la grilla semanal; no se valida (podría dejar fuera turnos de un horario especial más largo). Se acepta y queda documentado.
