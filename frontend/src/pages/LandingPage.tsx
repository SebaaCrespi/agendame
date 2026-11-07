import { Link } from 'react-router-dom';
import { Bell, CalendarDays, Check, MessageCircle, ShieldCheck, Sparkles } from 'lucide-react';
import { Brand } from '@/components/layout/Brand';
import { ThemeSwitch } from '@/components/layout/ThemeToggle';
import { buttonClass } from '@/components/ui/Button';
import { Badge } from '@/components/turnos/EstadoBadge';
import { DemoReserva } from '@/components/landing/DemoReserva';

const PARA_PROFESIONALES = [
  'Agenda del día con acciones rápidas',
  'Grilla semanal y excepciones (feriados, vacaciones)',
  'Reasignación y cancelación con motivo',
  'Historial completo de cada turno',
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-canvas">
      <header className="sticky top-0 z-30 border-b border-line bg-canvas/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Brand />
          <nav className="flex items-center gap-1 sm:gap-2" aria-label="Cuenta">
            <ThemeSwitch />
            <Link to="/reservar" className={buttonClass('ghost', 'md', 'hidden sm:inline-flex')}>
              Reservar
            </Link>
            <Link to="/login" className={buttonClass('ghost', 'md', 'hidden sm:inline-flex')}>
              Iniciar sesión
            </Link>
            <Link to="/register" className={buttonClass('primary', 'md')}>
              Crear cuenta
            </Link>
          </nav>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-14 pt-8 sm:px-6 md:pb-24 md:pt-12 lg:grid-cols-[1.1fr_1fr]">
          <div>
            <Badge className="bg-primary-soft text-primary" dot={false}>
              <Sparkles className="size-3.5" /> Con asistente virtual
            </Badge>
            <h1 className="mt-5 text-4xl font-semibold leading-[1.1] tracking-tight text-fg sm:text-5xl">
              Tus turnos, sin llamadas ni esperas.
            </h1>
            <p className="mt-5 max-w-lg text-base leading-relaxed text-muted sm:text-lg">
              Elegí profesional y horario sin registrarte. Creás tu cuenta solo al confirmar, y después gestionás tus turnos desde un solo lugar.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/reservar" className={buttonClass('primary', 'lg')}>
                Reservar un turno
              </Link>
              <Link to="/login" className={buttonClass('outline', 'lg')}>
                Ya tengo cuenta
              </Link>
            </div>
            <ul className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-[13px] text-muted">
              <li className="flex items-center gap-2"><ShieldCheck className="size-4 text-success" /> Cancelación hasta 2 h antes</li>
              <li className="flex items-center gap-2"><Bell className="size-4 text-success" /> Disponibilidad en tiempo real</li>
            </ul>
          </div>
          <DemoReserva />
        </section>

        {/* Asistente + profesionales */}
        <section className="mx-auto grid max-w-6xl gap-6 px-4 pb-16 sm:px-6 md:grid-cols-2 md:pb-20">
          <div className="rounded-xl border border-line bg-surface p-7">
            <span className="flex size-10 items-center justify-center rounded-lg bg-primary-soft text-primary">
              <MessageCircle className="size-5" aria-hidden="true" />
            </span>
            <h3 className="mt-4 text-lg font-semibold text-fg">Reservá conversando</h3>
            <p className="mt-2 text-muted">
              Escribile al asistente como le escribirías a la recepción: «¿Qué horarios tiene Juan mañana para un corte?». Busca horarios, reserva y cancela por vos.
            </p>
          </div>
          <div className="rounded-xl border border-line bg-surface p-7">
            <span className="flex size-10 items-center justify-center rounded-lg bg-primary-soft text-primary">
              <CalendarDays className="size-5" aria-hidden="true" />
            </span>
            <h3 className="mt-4 text-lg font-semibold text-fg">Para profesionales</h3>
            <ul className="mt-3 space-y-2">
              {PARA_PROFESIONALES.map((t) => (
                <li key={t} className="flex items-start gap-2 text-muted">
                  <Check className="mt-0.5 size-4 shrink-0 text-success" aria-hidden="true" /> {t}
                </li>
              ))}
            </ul>
            <Link to="/register?rol=PROVEEDOR" className={buttonClass('outline', 'md', 'mt-6')}>
              Sumarme como profesional
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-[13px] text-muted sm:px-6">
          <Brand />
          <p>© 2026 Agendame · Gestión de turnos</p>
        </div>
      </footer>
    </div>
  );
}
