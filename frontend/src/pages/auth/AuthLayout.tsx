import type { ReactNode } from 'react';
import { CalendarCheck, Clock, MessageCircle } from 'lucide-react';
import { Brand } from '@/components/layout/Brand';
import { ThemeSwitch } from '@/components/layout/ThemeToggle';

const PUNTOS = [
  { icon: CalendarCheck, texto: 'Reservá en tres pasos, solo con horarios libres' },
  { icon: Clock, texto: 'Cancelá sin cargo hasta 2 horas antes' },
  { icon: MessageCircle, texto: 'Asistente virtual para reservar conversando' },
];

/** Layout de login y registro: formulario a la izquierda, panel de marca a la derecha (desktop). */
export function AuthLayout({ title, description, children, footer }: { title: string; description: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="grid min-h-screen bg-canvas lg:grid-cols-2">
      <div className="flex flex-col px-4 py-6 sm:px-10">
        <div className="flex items-center justify-between">
          <Brand />
          <ThemeSwitch />
        </div>
        <div className="flex flex-1 items-center justify-center py-10">
          <div className="w-full max-w-sm">
            <h1 className="text-2xl font-semibold tracking-tight text-fg">{title}</h1>
            <p className="mt-1.5 text-muted">{description}</p>
            <div className="mt-8">{children}</div>
            <div className="mt-8 text-center text-[13px] text-muted">{footer}</div>
          </div>
        </div>
      </div>

      <aside className="relative hidden overflow-hidden border-l border-line bg-primary lg:flex lg:flex-col lg:justify-end lg:p-12">
        {/* Cuadrícula sutil de fondo, evoca una agenda */}
        <div
          className="absolute inset-0 opacity-[0.12]"
          style={{
            backgroundImage:
              'linear-gradient(to right, white 1px, transparent 1px), linear-gradient(to bottom, white 1px, transparent 1px)',
            backgroundSize: '56px 56px',
          }}
          aria-hidden="true"
        />
        <div className="relative max-w-md text-white">
          <p className="text-3xl font-semibold leading-tight tracking-tight">Tu agenda de turnos, clara y en un solo lugar.</p>
          <ul className="mt-8 space-y-4">
            {PUNTOS.map(({ icon: Icon, texto }) => (
              <li key={texto} className="flex items-center gap-3 text-[15px] text-white/90">
                <span className="flex size-9 items-center justify-center rounded-lg bg-white/15">
                  <Icon className="size-[18px]" aria-hidden="true" />
                </span>
                {texto}
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </div>
  );
}
