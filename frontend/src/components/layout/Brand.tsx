import { Link } from 'react-router-dom';
import { CalendarCheck } from 'lucide-react';
import { cn } from '@/utils/cn';

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn('flex size-8 items-center justify-center rounded-lg bg-primary text-on-primary', className)} aria-hidden="true">
      <CalendarCheck className="size-[18px]" strokeWidth={2} />
    </span>
  );
}

export function Brand({ to = '/', compact = false, className }: { to?: string; compact?: boolean; className?: string }) {
  return (
    <Link to={to} className={cn('flex items-center gap-2.5 rounded-lg', className)} aria-label="Agendame, inicio">
      <Logo />
      {!compact && <span className="text-[17px] font-semibold tracking-tight text-fg">Agendame</span>}
    </Link>
  );
}
