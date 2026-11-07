import type { ReactNode } from 'react';
import { AlertCircle, CheckCircle2, Info, TriangleAlert } from 'lucide-react';
import { cn } from '@/utils/cn';

type TipoAlerta = 'error' | 'ok' | 'info' | 'aviso';

interface AlertaProps {
  tipo: TipoAlerta;
  children: ReactNode;
  className?: string;
}

const estilos: Record<TipoAlerta, { clase: string; Icono: typeof Info }> = {
  error: { clase: 'bg-danger-soft text-danger', Icono: AlertCircle },
  ok: { clase: 'bg-success-soft text-success', Icono: CheckCircle2 },
  info: { clase: 'bg-info-soft text-info', Icono: Info },
  aviso: { clase: 'bg-warning-soft text-warning', Icono: TriangleAlert },
};

/** Aviso en línea. */
export function Alerta({ tipo, children, className }: AlertaProps) {
  const { clase, Icono } = estilos[tipo];
  return (
    <div
      role={tipo === 'error' ? 'alert' : 'status'}
      className={cn('flex items-start gap-2.5 rounded-lg px-3.5 py-3 text-[13px] font-medium', clase, className)}
    >
      <Icono className="mt-px size-4 shrink-0" aria-hidden="true" />
      <div className="min-w-0">{children}</div>
    </div>
  );
}
