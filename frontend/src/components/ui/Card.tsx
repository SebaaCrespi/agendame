import type { ReactNode } from 'react';
import { cn } from '@/utils/cn';

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const paddingStyles = {
  none: '',
  sm: 'p-4',
  md: 'p-5',
  lg: 'p-8',
};

export function Card({ children, className, padding = 'md' }: CardProps) {
  return (
    <div className={cn('rounded-xl border border-line bg-surface', paddingStyles[padding], className)}>{children}</div>
  );
}

export function CardHeader({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('mb-4', className)}>{children}</div>;
}

export function CardTitle({ children, className }: { children: ReactNode; className?: string }) {
  return <h2 className={cn('text-[15px] font-semibold text-fg', className)}>{children}</h2>;
}

export function CardDescription({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn('mt-0.5 text-[13px] text-muted', className)}>{children}</p>;
}

export function CardContent({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={className}>{children}</div>;
}

export function CardFooter({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('mt-5 flex items-center gap-2 border-t border-line pt-4', className)}>{children}</div>;
}

/** Cabecera de sección dentro de una card sin padding: título a la izquierda, acciones a la derecha. */
export function CardSection({ title, actions, className }: { title: ReactNode; actions?: ReactNode; className?: string }) {
  return (
    <div className={cn('flex min-h-[52px] items-center justify-between gap-3 border-b border-line px-5 py-3', className)}>
      <h2 className="text-[15px] font-semibold text-fg">{title}</h2>
      {actions}
    </div>
  );
}
