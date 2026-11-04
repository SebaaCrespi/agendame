import { addDays, format, isSameDay } from 'date-fns';
import { es } from 'date-fns/locale';
import { cn } from '@/utils/cn';
import { formatHora, minutosDelDia, parseHoraNegocio } from '@/utils/horaNegocio';
import { ESTADO_COLOR } from './estado';
import type { Turno } from '@/types';

const PX_POR_MIN = 1.2; // 30 min = 36 px

interface WeekGridProps {
  inicioSemana: Date; // lunes
  turnos: Turno[];
  desdeMin: number; // minutos desde medianoche (eje)
  hastaMin: number;
  selectedId?: number | null;
  onSelect: (turno: Turno) => void;
}

/** Grilla semanal (lunes a domingo) con los turnos ubicados por día y hora. */
export function WeekGrid({ inicioSemana, turnos, desdeMin, hastaMin, selectedId, onSelect }: WeekGridProps) {
  const dias = Array.from({ length: 7 }, (_, i) => addDays(inicioSemana, i));
  const horas: number[] = [];
  for (let m = Math.floor(desdeMin / 60) * 60; m < hastaMin; m += 60) horas.push(m);
  const alto = (hastaMin - desdeMin) * PX_POR_MIN;
  const hoy = new Date();

  return (
    // Scroll horizontal propio: en pantallas angostas la página no se desborda
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="min-w-[720px]">
        {/* Encabezado de días */}
        <div className="grid grid-cols-[48px_repeat(7,1fr)] border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div />
          {dias.map((dia) => (
            <div
              key={dia.toISOString()}
              className={cn(
                'py-2 text-center text-xs font-medium capitalize',
                isSameDay(dia, hoy) ? 'text-indigo-600 dark:text-indigo-400' : 'text-gray-600 dark:text-gray-300'
              )}
            >
              {format(dia, 'EEE d', { locale: es })}
            </div>
          ))}
        </div>

        {/* Cuerpo */}
        <div className="grid grid-cols-[48px_repeat(7,1fr)]">
          {/* Eje de horas */}
          <div className="relative" style={{ height: alto }}>
            {horas.map((m) => (
              <div
                key={m}
                className="absolute right-1 -translate-y-2 text-[10px] text-gray-400"
                style={{ top: (m - desdeMin) * PX_POR_MIN }}
              >
                {String(m / 60).padStart(2, '0')}:00
              </div>
            ))}
          </div>

          {dias.map((dia) => {
            const delDia = turnos.filter((t) => isSameDay(parseHoraNegocio(t.fecha_inicio), dia));
            return (
              <div
                key={dia.toISOString()}
                className="relative border-l border-gray-100 dark:border-gray-800"
                style={{ height: alto }}
              >
                {horas.map((m) => (
                  <div
                    key={m}
                    className="absolute inset-x-0 border-t border-gray-100 dark:border-gray-800"
                    style={{ top: (m - desdeMin) * PX_POR_MIN }}
                  />
                ))}
                {delDia.map((t) => {
                  const ini = Math.max(minutosDelDia(t.fecha_inicio), desdeMin);
                  const fin = Math.min(minutosDelDia(t.fecha_fin), hastaMin);
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => onSelect(t)}
                      title={`${formatHora(t.fecha_inicio)} ${t.cliente_nombre} - ${t.servicio_nombre}`}
                      className={cn(
                        'absolute inset-x-0.5 overflow-hidden rounded border px-1 py-0.5 text-left text-[11px] leading-tight transition-shadow hover:shadow-md',
                        ESTADO_COLOR[t.estado],
                        selectedId === t.id && 'ring-2 ring-indigo-500'
                      )}
                      style={{ top: (ini - desdeMin) * PX_POR_MIN, height: Math.max((fin - ini) * PX_POR_MIN, 18) }}
                    >
                      <span className="font-semibold">{formatHora(t.fecha_inicio)}</span> {t.cliente_nombre}
                      <span className="block truncate opacity-80">{t.servicio_nombre}</span>
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
