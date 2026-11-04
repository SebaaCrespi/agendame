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

/** Clases de color por estado (bloque de grilla y badges). */
export const ESTADO_COLOR: Record<TurnoEstado, string> = {
  PENDIENTE: 'bg-yellow-100 text-yellow-900 border-yellow-300 dark:bg-yellow-900/40 dark:text-yellow-100 dark:border-yellow-700',
  CONFIRMADO: 'bg-green-100 text-green-900 border-green-300 dark:bg-green-900/40 dark:text-green-100 dark:border-green-700',
  EN_CURSO: 'bg-blue-100 text-blue-900 border-blue-300 dark:bg-blue-900/40 dark:text-blue-100 dark:border-blue-700',
  FINALIZADO: 'bg-gray-100 text-gray-800 border-gray-300 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-600',
  CANCELADO_CLIENTE: 'bg-red-50 text-red-800 border-red-200 line-through dark:bg-red-900/20 dark:text-red-300 dark:border-red-800',
  CANCELADO_PROFESIONAL: 'bg-orange-50 text-orange-800 border-orange-200 line-through dark:bg-orange-900/20 dark:text-orange-300 dark:border-orange-800',
  NO_ASISTIO: 'bg-gray-50 text-gray-500 border-gray-200 dark:bg-gray-900 dark:text-gray-400 dark:border-gray-700',
};

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
