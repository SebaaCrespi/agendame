import { NavLink, Outlet } from 'react-router-dom';
import { CalendarClock, Stethoscope, UserRound } from 'lucide-react';
import { PageHeader } from '@/components/ui/misc';
import { cn } from '@/utils/cn';

const TABS = [
  { to: 'servicios', label: 'Servicios', icon: Stethoscope },
  { to: 'disponibilidad', label: 'Disponibilidad', icon: CalendarClock },
  { to: 'perfil', label: 'Perfil', icon: UserRound },
];

/** CU-02: configuración del profesional, con pestañas. */
export function ConfiguracionLayout() {
  return (
    <>
      <PageHeader title="Configuración" description="Lo que ofrecés, cuándo atendés y cómo te ven los clientes." />
      <nav aria-label="Secciones de configuración" className="mb-6 flex gap-1 overflow-x-auto overflow-y-hidden border-b border-line [scrollbar-width:none]">
        {TABS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                '-mb-px flex shrink-0 items-center gap-2 border-b-2 px-3 py-2.5 text-sm font-medium transition-colors',
                isActive ? 'border-primary text-primary' : 'border-transparent text-muted hover:text-fg'
              )
            }
          >
            <Icon className="size-4" aria-hidden="true" />
            {label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </>
  );
}
