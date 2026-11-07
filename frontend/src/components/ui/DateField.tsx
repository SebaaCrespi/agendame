import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { DayPicker } from 'react-day-picker';
import { es } from 'react-day-picker/locale';
import { format, isValid, parse } from 'date-fns';
import { CalendarDays, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { cn } from '@/utils/cn';
import { fieldClass, Label } from './Input';

interface DateFieldProps {
  /** Fecha en formato AAAA-MM-DD ('' si no hay). */
  value: string;
  onChange: (value: string) => void;
  min?: string;
  max?: string;
  label?: string;
  id?: string;
  required?: boolean;
  placeholder?: string;
  className?: string;
  'aria-label'?: string;
  title?: string;
}

const ISO = 'yyyy-MM-dd';
const ANCHO_POPOVER = 300;

function aFecha(v?: string): Date | undefined {
  if (!v) return undefined;
  const d = parse(v, ISO, new Date());
  return isValid(d) ? d : undefined;
}

/** Selector de fecha con calendario propio (reemplaza al input date nativo). */
export function DateField({
  value,
  onChange,
  min,
  max,
  label,
  id,
  required,
  placeholder = 'Elegí una fecha',
  className,
  title,
  'aria-label': ariaLabel,
}: DateFieldProps) {
  const autoId = useId();
  const fieldId = id || autoId;
  const [abierto, setAbierto] = useState(false);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);
  const botonRef = useRef<HTMLButtonElement>(null);
  const popRef = useRef<HTMLDivElement>(null);

  const seleccionada = aFecha(value);
  const desde = aFecha(min);
  const hasta = aFecha(max);
  const [hoy] = useState(() => new Date());
  const hoyDeshabilitado = (desde && format(hoy, ISO) < format(desde, ISO)) || (hasta && format(hoy, ISO) > format(hasta, ISO));

  // Ubica el calendario debajo del campo (o arriba si no entra), fijo a la ventana
  // para que no lo recorte un contenedor con scroll como el diálogo.
  useLayoutEffect(() => {
    if (!abierto || !botonRef.current) return;
    const r = botonRef.current.getBoundingClientRect();
    const alto = popRef.current?.offsetHeight ?? 360;
    const abajo = r.bottom + 6;
    const top = abajo + alto > window.innerHeight - 8 && r.top - alto - 6 > 8 ? r.top - alto - 6 : abajo;
    const left = Math.max(8, Math.min(r.left, window.innerWidth - ANCHO_POPOVER - 8));
    setPos({ top, left });
  }, [abierto]);

  useEffect(() => {
    if (!abierto) return;
    const cerrar = () => setAbierto(false);
    const clickAfuera = (e: MouseEvent) => {
      const t = e.target as Node;
      if (!popRef.current?.contains(t) && !botonRef.current?.contains(t)) cerrar();
    };
    const tecla = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        cerrar();
        botonRef.current?.focus();
      }
    };
    const scroll = (e: Event) => {
      if (!popRef.current?.contains(e.target as Node)) cerrar();
    };
    document.addEventListener('mousedown', clickAfuera);
    document.addEventListener('keydown', tecla, true);
    window.addEventListener('scroll', scroll, true);
    window.addEventListener('resize', cerrar);
    return () => {
      document.removeEventListener('mousedown', clickAfuera);
      document.removeEventListener('keydown', tecla, true);
      window.removeEventListener('scroll', scroll, true);
      window.removeEventListener('resize', cerrar);
    };
  }, [abierto]);

  const elegir = (d: Date | undefined) => {
    onChange(d ? format(d, ISO) : '');
    setAbierto(false);
    botonRef.current?.focus();
  };

  const texto = seleccionada ? format(seleccionada, 'dd/MM/yyyy') : '';

  return (
    <div className={cn('w-full', className)}>
      {label && <Label htmlFor={fieldId}>{label}</Label>}
      <div className="relative">
        <button
          ref={botonRef}
          id={fieldId}
          type="button"
          onClick={() => setAbierto((a) => !a)}
          aria-haspopup="dialog"
          aria-expanded={abierto}
          aria-label={ariaLabel ? `${ariaLabel}${texto ? `: ${texto}` : ''}` : undefined}
          title={title}
          className={cn(fieldClass, 'flex h-10 items-center gap-2 pl-3 text-left', value && !required ? 'pr-9' : 'pr-3')}
        >
          <CalendarDays className="size-4 shrink-0 text-subtle" aria-hidden="true" />
          <span className={cn('truncate tabular', !texto && 'text-subtle')}>{texto || ariaLabel || placeholder}</span>
        </button>
        {value && !required && (
          <button
            type="button"
            onClick={() => onChange('')}
            aria-label={`Borrar ${ariaLabel?.toLowerCase() ?? 'fecha'}`}
            className="absolute inset-y-0 right-1 my-auto flex size-8 items-center justify-center rounded-md text-subtle transition-colors hover:bg-surface-2 hover:text-fg"
          >
            <X className="size-3.5" aria-hidden="true" />
          </button>
        )}
        {/* Para que la validación nativa del formulario siga funcionando */}
        {required && (
          <input
            tabIndex={-1}
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 opacity-0"
            value={value}
            required
            onChange={() => {}}
            onInvalid={() => setAbierto(true)}
          />
        )}
      </div>

      {abierto &&
        createPortal(
          <div
            ref={popRef}
            role="dialog"
            aria-label={ariaLabel ?? label ?? 'Elegir fecha'}
            style={{ top: pos?.top ?? -9999, left: pos?.left ?? -9999, width: ANCHO_POPOVER }}
            className="fixed z-[70] rounded-xl border border-line bg-surface p-3 text-fg shadow-pop"
          >
            <DayPicker
              mode="single"
              locale={es}
              autoFocus
              selected={seleccionada}
              onSelect={elegir}
              defaultMonth={seleccionada ?? desde ?? hoy}
              disabled={[...(desde ? [{ before: desde }] : []), ...(hasta ? [{ after: hasta }] : [])]}
              startMonth={desde}
              endMonth={hasta}
              showOutsideDays
              components={{
                Chevron: ({ orientation }) =>
                  orientation === 'left' ? <ChevronLeft className="size-4" /> : <ChevronRight className="size-4" />,
              }}
              classNames={{
                root: 'relative',
                months: 'relative',
                month_caption: 'flex h-8 items-center px-1',
                caption_label: 'text-sm font-semibold capitalize',
                nav: 'absolute right-0 top-0 z-10 flex gap-1',
                button_previous: 'flex size-8 items-center justify-center rounded-md text-muted hover:bg-surface-2 hover:text-fg disabled:opacity-30 disabled:hover:bg-transparent',
                button_next: 'flex size-8 items-center justify-center rounded-md text-muted hover:bg-surface-2 hover:text-fg disabled:opacity-30 disabled:hover:bg-transparent',
                month_grid: 'mt-2 w-full border-collapse',
                weekdays: '',
                weekday: 'pb-1 text-[11px] font-medium uppercase text-subtle',
                week: '',
                day: 'p-0.5 text-center text-sm',
                day_button:
                  'mx-auto flex size-9 items-center justify-center rounded-lg tabular transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring',
                today: 'font-semibold text-primary',
                selected: '[&>button]:bg-primary [&>button]:text-on-primary [&>button]:hover:bg-primary-hover',
                outside: 'text-subtle opacity-50',
                disabled: 'pointer-events-none opacity-30',
                hidden: 'invisible',
              }}
            />
            <div className="mt-2 flex justify-between border-t border-line pt-2">
              {!required ? (
                <button type="button" onClick={() => elegir(undefined)} className="rounded-md px-2 py-1 text-[13px] font-medium text-muted hover:bg-surface-2 hover:text-fg">
                  Borrar
                </button>
              ) : (
                <span />
              )}
              <button
                type="button"
                disabled={!!hoyDeshabilitado}
                onClick={() => elegir(hoy)}
                className="rounded-md px-2 py-1 text-[13px] font-medium text-primary hover:bg-primary-soft disabled:opacity-40 disabled:hover:bg-transparent"
              >
                Hoy
              </button>
            </div>
          </div>,
          document.body
        )}
    </div>
  );
}
