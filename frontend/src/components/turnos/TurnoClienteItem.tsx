import { Clock, RotateCcw, UserRound, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';
import { capitalizar, fmt } from '@/utils/formato';
import { formatHora, parseHoraNegocio } from '@/utils/horaNegocio';
import { ES_CANCELADO } from './estado';
import { EstadoBadge } from './EstadoBadge';
import type { Turno } from '@/types';

const CANCELACION_HORAS_ANTES = 2;

/** El backend permite cancelar PENDIENTE/CONFIRMADO con más de 2 h de antelación. */
export function puedeCancelar(turno: Turno, ahora: Date): boolean {
  if (turno.estado !== 'PENDIENTE' && turno.estado !== 'CONFIRMADO') return false;
  const horas = (parseHoraNegocio(turno.fecha_inicio).getTime() - ahora.getTime()) / 3_600_000;
  return horas > CANCELACION_HORAS_ANTES;
}

/** Fila de un turno del cliente: fecha en bloque, servicio, profesional, estado y acción. */
export function TurnoClienteItem({ turno, onCancelar }: { turno: Turno; onCancelar?: () => void }) {
  const inicio = parseHoraNegocio(turno.fecha_inicio);
  const cancelado = ES_CANCELADO(turno.estado);
  return (
    <li className="flex flex-wrap items-center gap-4 px-5 py-4">
      <div
        className={cn(
          'flex size-14 shrink-0 flex-col items-center justify-center rounded-xl border',
          cancelado ? 'border-line bg-surface-2 text-subtle' : 'border-primary/20 bg-primary-soft text-primary'
        )}
      >
        <span className="text-[11px] font-medium uppercase leading-none">{fmt(inicio, 'MMM')}</span>
        <span className="mt-0.5 text-xl font-semibold leading-none tabular">{fmt(inicio, 'd')}</span>
      </div>
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className={cn('truncate font-medium text-fg', cancelado && 'text-muted line-through')}>{turno.servicio_nombre}</p>
          <EstadoBadge estado={turno.estado} />
        </div>
        <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px] text-muted">
          <span className="flex items-center gap-1.5">
            <Clock className="size-3.5" aria-hidden="true" />
            {capitalizar(fmt(inicio, 'EEEE'))} · {formatHora(turno.fecha_inicio)} – {formatHora(turno.fecha_fin)}
          </span>
          <span className="flex items-center gap-1.5">
            <UserRound className="size-3.5" aria-hidden="true" />
            {turno.profesional_nombre}
          </span>
        </p>
        {turno.motivo_cancelacion && <p className="text-[13px] text-muted">Motivo: {turno.motivo_cancelacion}</p>}
        {turno.reasignado_desde && (
          <p className="flex items-center gap-1.5 text-[13px] text-info">
            <RotateCcw className="size-3.5" aria-hidden="true" />
            Reprogramado: antes era el {fmt(parseHoraNegocio(turno.reasignado_desde), "d MMM, HH:mm")}
            {turno.motivo_reasignacion && ` (${turno.motivo_reasignacion})`}
          </p>
        )}
      </div>
      {onCancelar && (
        <Button variant="outline" size="sm" onClick={onCancelar} className="max-sm:ml-[4.5rem]">
          <XCircle /> Cancelar
        </Button>
      )}
    </li>
  );
}
