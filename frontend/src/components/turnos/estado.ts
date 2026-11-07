import type { TurnoEstado } from '@/types';

export const ESTADO_LABEL: Record<TurnoEstado, string> = {
  PENDIENTE: 'Pendiente',
  CONFIRMADO: 'Confirmado',
  EN_CURSO: 'En curso',
  FINALIZADO: 'Finalizado',
  CANCELADO_CLIENTE: 'Cancelado por cliente',
  CANCELADO_PROFESIONAL: 'Cancelado por profesional',
  NO_ASISTIO: 'No asistió',
};

/** Tono de cada estado: badge con fondo suave y punto de color. */
export const ESTADO_TONO: Record<TurnoEstado, string> = {
  PENDIENTE: 'bg-warning-soft text-warning',
  CONFIRMADO: 'bg-success-soft text-success',
  EN_CURSO: 'bg-info-soft text-info',
  FINALIZADO: 'bg-surface-2 text-muted',
  CANCELADO_CLIENTE: 'bg-danger-soft text-danger',
  CANCELADO_PROFESIONAL: 'bg-danger-soft text-danger',
  NO_ASISTIO: 'bg-surface-2 text-muted',
};

/** Color de la barra lateral de un turno en la grilla. */
export const ESTADO_BARRA: Record<TurnoEstado, string> = {
  PENDIENTE: 'border-l-warning',
  CONFIRMADO: 'border-l-success',
  EN_CURSO: 'border-l-info',
  FINALIZADO: 'border-l-subtle',
  CANCELADO_CLIENTE: 'border-l-danger',
  CANCELADO_PROFESIONAL: 'border-l-danger',
  NO_ASISTIO: 'border-l-subtle',
};

/** Color sólido del estado (puntos y barras de resumen). */
export const ESTADO_PUNTO: Record<TurnoEstado, string> = {
  PENDIENTE: 'bg-warning',
  CONFIRMADO: 'bg-success',
  EN_CURSO: 'bg-info',
  FINALIZADO: 'bg-subtle',
  CANCELADO_CLIENTE: 'bg-danger',
  CANCELADO_PROFESIONAL: 'bg-danger',
  NO_ASISTIO: 'bg-line-strong',
};

export const ES_CANCELADO = (e: TurnoEstado) => e === 'CANCELADO_CLIENTE' || e === 'CANCELADO_PROFESIONAL';

/**
 * Cambios de estado que ofrece la UI del proveedor (copia de
 * TurnoService.TRANSICIONES_VALIDAS en el backend, sin las cancelaciones,
 * que son CU-08). El backend sigue validando.
 */
export const TRANSICIONES: Record<TurnoEstado, TurnoEstado[]> = {
  PENDIENTE: ['CONFIRMADO'],
  CONFIRMADO: ['EN_CURSO', 'NO_ASISTIO'],
  EN_CURSO: ['FINALIZADO', 'NO_ASISTIO'],
  FINALIZADO: [],
  CANCELADO_CLIENTE: [],
  CANCELADO_PROFESIONAL: [],
  NO_ASISTIO: [],
};

export const ACCION_LABEL: Partial<Record<TurnoEstado, string>> = {
  CONFIRMADO: 'Confirmar',
  EN_CURSO: 'Iniciar atención',
  FINALIZADO: 'Finalizar',
  NO_ASISTIO: 'Marcar ausente',
};

export const ESTADOS: TurnoEstado[] = Object.keys(ESTADO_LABEL) as TurnoEstado[];

/** Grupos de estado del historial (CU-09). */
export const GRUPOS_ESTADO = {
  todos: { label: 'Todos', estados: undefined },
  activos: { label: 'Activos', estados: ['PENDIENTE', 'CONFIRMADO', 'EN_CURSO'] },
  finalizados: { label: 'Finalizados', estados: ['FINALIZADO'] },
  cancelados: { label: 'Cancelados', estados: ['CANCELADO_CLIENTE', 'CANCELADO_PROFESIONAL'] },
  ausentes: { label: 'No asistió', estados: ['NO_ASISTIO'] },
} as const satisfies Record<string, { label: string; estados: readonly TurnoEstado[] | undefined }>;

export type GrupoEstado = keyof typeof GRUPOS_ESTADO;

/** Estados del grupo como lista mutable para los filtros de la API. */
export function estadosDelGrupo(grupo: GrupoEstado): TurnoEstado[] | undefined {
  const estados = GRUPOS_ESTADO[grupo].estados;
  return estados ? [...estados] : undefined;
}

/**
 * El asistente puede reservar o cancelar turnos desde cualquier pantalla del
 * cliente: este evento avisa a las páginas que muestran turnos que recarguen.
 */
export const EVENTO_TURNOS_CAMBIARON = 'agendame:turnos-cambiaron';
