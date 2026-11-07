import type { ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/utils/cn';

/** Título de página con descripción y acciones. */
export function PageHeader({
  title,
  description,
  actions,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('mb-6 flex flex-wrap items-end justify-between gap-4', className)}>
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight text-fg">{title}</h1>
        {description && <p className="mt-1 text-muted">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Spinner({ className, label = 'Cargando' }: { className?: string; label?: string }) {
  return (
    <div className={cn('flex justify-center py-10 text-muted', className)} role="status">
      <Loader2 className="size-6 animate-spin" aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('animate-pulse rounded-md bg-surface-2', className)} aria-hidden="true" />;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon?: LucideIcon;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('flex flex-col items-center px-6 py-12 text-center', className)}>
      {Icon && (
        <span className="mb-4 flex size-11 items-center justify-center rounded-full bg-surface-2 text-muted">
          <Icon className="size-5" aria-hidden="true" />
        </span>
      )}
      <p className="font-medium text-fg">{title}</p>
      {description && <p className="mt-1 max-w-sm text-[13px] text-muted">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

/** Control segmentado (pestañas compactas). */
export function Segmented<T extends string>({
  value,
  options,
  onChange,
  label,
  className,
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
  label: string;
  className?: string;
}) {
  return (
    <div role="tablist" aria-label={label} className={cn('inline-flex rounded-lg bg-surface-2 p-1', className)}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="tab"
          aria-selected={value === o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            'h-8 rounded-md px-3 text-[13px] font-medium transition-colors',
            value === o.value ? 'bg-surface text-fg shadow-sm' : 'text-muted hover:text-fg'
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Tarjeta de métrica. */
export function Stat({ label, value, hint, icon: Icon }: { label: string; value: ReactNode; hint?: ReactNode; icon?: LucideIcon }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[13px] text-muted">{label}</p>
        {Icon && <Icon className="size-4 text-subtle" aria-hidden="true" />}
      </div>
      <p className="mt-1 text-2xl font-semibold tracking-tight text-fg tabular">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-muted">{hint}</p>}
    </div>
  );
}

/** Avatar con iniciales o foto. */
export function Avatar({ nombre, src, size = 'md', className }: { nombre: string; src?: string | null; size?: 'sm' | 'md' | 'lg'; className?: string }) {
  const iniciales = nombre
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join('');
  const dims = { sm: 'size-8 text-xs', md: 'size-10 text-sm', lg: 'size-12 text-base' }[size];
  if (src) {
    return <img src={src} alt="" className={cn('shrink-0 rounded-full object-cover', dims, className)} />;
  }
  return (
    <span
      className={cn('flex shrink-0 items-center justify-center rounded-full bg-primary-soft font-semibold text-primary', dims, className)}
      aria-hidden="true"
    >
      {iniciales || '?'}
    </span>
  );
}
