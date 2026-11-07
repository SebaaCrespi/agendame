import { addDays, isSameDay } from 'date-fns';
import { cn } from '@/utils/cn';
import { capitalizar, fmt } from '@/utils/formato';
import { formatHora, minutosDelDia, parseHoraNegocio } from '@/utils/horaNegocio';
import { ES_CANCELADO, ESTADO_BARRA } from './estado';
import type { Turno } from '@/types';

const PX_POR_MIN = 1.4; // 30 min = 42 px

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
  const ahora = new Date();
  const minAhora = ahora.getHours() * 60 + ahora.getMinutes();

  return (
    // Scroll horizontal propio: en pantallas angostas la página no se desborda
    <div className="overflow-x-auto">
      <div className="min-w-[760px]">
        <div className="grid grid-cols-[52px_repeat(7,1fr)] border-b border-line">
          <div />
          {dias.map((dia) => {
            const esHoy = isSameDay(dia, ahora);
            return (
              <div key={dia.toISOString()} className="flex flex-col items-center py-2.5">
                <span className={cn('text-[11px] font-medium uppercase', esHoy ? 'text-primary' : 'text-muted')}>
                  {capitalizar(fmt(dia, 'EEE'))}
                </span>
                <span
                  className={cn(
                    'mt-0.5 flex size-7 items-center justify-center rounded-full text-sm font-semibold tabular',
                    esHoy ? 'bg-primary text-on-primary' : 'text-fg'
                  )}
                >
                  {fmt(dia, 'd')}
                </span>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-[52px_repeat(7,1fr)]">
          <div className="relative" style={{ height: alto }}>
            {horas.map((m) => (
              <div key={m} className="absolute right-2 -translate-y-2 text-[11px] text-subtle tabular" style={{ top: (m - desdeMin) * PX_POR_MIN }}>
                {String(m / 60).padStart(2, '0')}:00
              </div>
            ))}
          </div>

          {dias.map((dia) => {
            const delDia = turnos.filter((t) => isSameDay(parseHoraNegocio(t.fecha_inicio), dia));
            const esHoy = isSameDay(dia, ahora);
            return (
              <div key={dia.toISOString()} className={cn('relative border-l border-line', esHoy && 'bg-primary-soft/40')} style={{ height: alto }}>
                {horas.map((m) => (
                  <div key={m} className="absolute inset-x-0 border-t border-line/70" style={{ top: (m - desdeMin) * PX_POR_MIN }} />
                ))}
                {esHoy && minAhora >= desdeMin && minAhora <= hastaMin && (
                  <div className="absolute inset-x-0 z-10 h-px bg-danger" style={{ top: (minAhora - desdeMin) * PX_POR_MIN }} aria-hidden="true">
                    <span className="absolute -left-1 -top-1 size-2 rounded-full bg-danger" />
                  </div>
                )}
                {delDia.map((t) => {
                  const ini = Math.max(minutosDelDia(t.fecha_inicio), desdeMin);
                  const fin = Math.min(minutosDelDia(t.fecha_fin), hastaMin);
                  const cancelado = ES_CANCELADO(t.estado);
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => onSelect(t)}
                      title={`${formatHora(t.fecha_inicio)} ${t.cliente_nombre} · ${t.servicio_nombre}`}
                      className={cn(
                        'absolute inset-x-1 overflow-hidden rounded-md border border-l-[3px] border-line bg-surface px-1.5 py-1 text-left text-[11px] leading-tight shadow-sm transition-shadow hover:shadow-md',
                        ESTADO_BARRA[t.estado],
                        cancelado && 'bg-surface-2 text-subtle',
                        selectedId === t.id && 'ring-2 ring-primary'
                      )}
                      style={{ top: (ini - desdeMin) * PX_POR_MIN + 1, height: Math.max((fin - ini) * PX_POR_MIN - 2, 20) }}
                    >
                      <span className={cn('block truncate font-semibold text-fg', cancelado && 'text-subtle line-through')}>
                        <span className="tabular">{formatHora(t.fecha_inicio)}</span> {t.cliente_nombre}
                      </span>
                      <span className="block truncate text-muted">{t.servicio_nombre}</span>
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
