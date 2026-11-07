import { cn } from '@/utils/cn';
import { ESTADO_LABEL, ESTADO_TONO } from './estado';
import type { TurnoEstado } from '@/types';

/** Badge del estado de un turno: fondo suave + punto de color. */
export function EstadoBadge({ estado, className }: { estado: TurnoEstado; className?: string }) {
  return <Badge className={cn(ESTADO_TONO[estado], className)}>{ESTADO_LABEL[estado]}</Badge>;
}

export function Badge({ children, className, dot = true }: { children: React.ReactNode; className?: string; dot?: boolean }) {
  return (
    <span
      className={cn(
        'inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium',
        className
      )}
    >
      {dot && <span className="size-1.5 rounded-full bg-current" aria-hidden="true" />}
      {children}
    </span>
  );
}
