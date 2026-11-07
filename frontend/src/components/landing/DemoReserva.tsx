import { useEffect, useState } from 'react';
import { CalendarCheck, CalendarDays, Check, Clock, Stethoscope, UserRound } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/utils/cn';

const PASOS: { titulo: string; icon: LucideIcon }[] = [
  { titulo: 'Elegí profesional', icon: UserRound },
  { titulo: 'Elegí el servicio', icon: Stethoscope },
  { titulo: 'Elegí día y hora', icon: CalendarDays },
  { titulo: 'Listo, reservado', icon: CalendarCheck },
];

/** Cada paso dura dos "tics": primero se muestra, después se marca la elección. */
const TIC_MS = 1400;

function usePrefiereMenosMovimiento() {
  const [reducir, setReducir] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const h = () => setReducir(mq.matches);
    mq.addEventListener('change', h);
    return () => mq.removeEventListener('change', h);
  }, []);
  return reducir;
}

/**
 * Demo de la reserva en loop: recorre los pasos como si alguien estuviera
 * reservando. Con "reducir movimiento" no avanza sola y se navega con los pasos.
 */
export function DemoReserva() {
  const reducir = usePrefiereMenosMovimiento();
  const [tic, setTic] = useState(0);

  useEffect(() => {
    if (reducir) return;
    const t = setInterval(() => setTic((x) => (x + 1) % (PASOS.length * 2)), TIC_MS);
    return () => clearInterval(t);
  }, [reducir]);

  const paso = Math.floor(tic / 2);
  const elegido = tic % 2 === 1 || reducir;

  return (
    <div
      className="rounded-2xl border border-line bg-surface shadow-pop"
      role="region"
      aria-label="Demostración de cómo reservar un turno"
    >
      {/* Pasos con barra de progreso */}
      <ol className="grid grid-cols-4 gap-2 border-b border-line p-4">
        {PASOS.map((p, i) => (
          <li key={p.titulo}>
            <button
              type="button"
              onClick={() => setTic(i * 2 + 1)}
              className="group w-full text-left"
              aria-current={i === paso ? 'step' : undefined}
            >
              <span className="block h-1 overflow-hidden rounded-full bg-surface-2">
                <span
                  key={i === paso ? tic : undefined}
                  className={cn(
                    'block h-full rounded-full bg-primary',
                    i < paso && 'w-full',
                    i > paso && 'w-0',
                    i === paso && (reducir ? 'w-full' : 'w-0 animate-[demo-progreso_2800ms_linear_forwards]')
                  )}
                  style={i === paso && !reducir && tic % 2 === 1 ? { animationDelay: `-${TIC_MS}ms` } : undefined}
                />
              </span>
              <span className={cn('mt-2 hidden text-xs font-medium transition-colors sm:block', i === paso ? 'text-fg' : 'text-subtle group-hover:text-muted')}>
                {p.titulo}
              </span>
            </button>
          </li>
        ))}
      </ol>

      <div className="relative h-[300px] overflow-hidden p-5" aria-live="polite">
        <p className="mb-4 flex items-center gap-2 text-sm font-semibold text-fg sm:hidden">{PASOS[paso].titulo}</p>
        <div key={paso} className="motion-safe:animate-[demo-entrada_400ms_ease-out]">
          {paso === 0 && <EscenaProfesional elegido={elegido} />}
          {paso === 1 && <EscenaServicio elegido={elegido} />}
          {paso === 2 && <EscenaHorario elegido={elegido} />}
          {paso === 3 && <EscenaListo />}
        </div>
      </div>
    </div>
  );
}

function Opcion({ activo, children }: { activo: boolean; children: React.ReactNode }) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-xl border p-3 transition-all duration-300',
        activo ? 'border-primary bg-primary-soft motion-safe:scale-[1.02]' : 'border-line bg-surface'
      )}
    >
      {children}
    </div>
  );
}

function EscenaProfesional({ elegido }: { elegido: boolean }) {
  const pros = [
    { ini: 'PR', nombre: 'Dra. Paula Ríos', esp: 'Clínica médica' },
    { ini: 'JF', nombre: 'Juan Ferrari', esp: 'Kinesiología' },
    { ini: 'ML', nombre: 'Marta Luna', esp: 'Nutrición' },
  ];
  return (
    <div className="space-y-2.5">
      {pros.map((p, i) => (
        <Opcion key={p.ini} activo={elegido && i === 0}>
          <span className="flex size-9 items-center justify-center rounded-full bg-primary-soft text-xs font-semibold text-primary">{p.ini}</span>
          <span className="min-w-0 flex-1">
            <span className="block text-sm font-medium text-fg">{p.nombre}</span>
            <span className="block text-xs text-muted">{p.esp}</span>
          </span>
          {elegido && i === 0 && <Tilde />}
        </Opcion>
      ))}
    </div>
  );
}

function EscenaServicio({ elegido }: { elegido: boolean }) {
  const servicios = [
    { nombre: 'Consulta general', dur: '30 min', precio: '$ 18.000' },
    { nombre: 'Control', dur: '20 min', precio: '$ 12.000' },
    { nombre: 'Primera consulta', dur: '45 min', precio: '$ 24.000' },
  ];
  return (
    <div className="space-y-2.5">
      {servicios.map((s, i) => (
        <Opcion key={s.nombre} activo={elegido && i === 0}>
          <span className="min-w-0 flex-1">
            <span className="block text-sm font-medium text-fg">{s.nombre}</span>
            <span className="flex items-center gap-1 text-xs text-muted">
              <Clock className="size-3" aria-hidden="true" /> {s.dur}
            </span>
          </span>
          <span className="text-sm font-semibold text-fg tabular">{s.precio}</span>
        </Opcion>
      ))}
    </div>
  );
}

function EscenaHorario({ elegido }: { elegido: boolean }) {
  const dias = [
    { d: 'Lu', n: 9 },
    { d: 'Ma', n: 10 },
    { d: 'Mi', n: 11 },
    { d: 'Ju', n: 12 },
    { d: 'Vi', n: 13 },
  ];
  const horarios = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '14:00', '14:30'];
  const ocupados = new Set(['09:00', '10:00', '14:30']);
  return (
    <div>
      <div className="grid grid-cols-5 gap-2">
        {dias.map((x) => (
          <span
            key={x.n}
            className={cn(
              'flex flex-col items-center rounded-lg border py-1.5',
              x.n === 10 ? 'border-primary bg-primary-soft text-primary' : 'border-line text-fg'
            )}
          >
            <span className="text-[10px] font-medium uppercase opacity-70">{x.d}</span>
            <span className="text-sm font-semibold tabular">{x.n}</span>
          </span>
        ))}
      </div>
      <div className="mt-4 grid grid-cols-4 gap-2">
        {horarios.map((h) => {
          const sel = elegido && h === '10:30';
          return (
            <span
              key={h}
              className={cn(
                'flex h-9 items-center justify-center rounded-lg text-[13px] font-medium tabular transition-all duration-300',
                sel && 'bg-primary text-on-primary motion-safe:scale-105',
                !sel && ocupados.has(h) && 'bg-surface-2 text-subtle line-through',
                !sel && !ocupados.has(h) && 'border border-line text-fg'
              )}
            >
              {h}
            </span>
          );
        })}
      </div>
    </div>
  );
}

function EscenaListo() {
  return (
    <div className="flex h-full flex-col items-center pt-4 text-center">
      <span className="flex size-14 items-center justify-center rounded-full bg-success-soft text-success motion-safe:animate-[demo-pop_500ms_ease-out]">
        <Check className="size-7" strokeWidth={2.5} aria-hidden="true" />
      </span>
      <p className="mt-4 text-lg font-semibold text-fg">¡Turno reservado!</p>
      <p className="mt-1 text-sm text-muted">Consulta general con Dra. Paula Ríos</p>
      <p className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary-soft px-3 py-2 text-[13px] font-medium text-primary">
        <CalendarDays className="size-4" aria-hidden="true" /> Martes 10 de noviembre · 10:30
      </p>
    </div>
  );
}

function Tilde() {
  return (
    <span className="flex size-5 items-center justify-center rounded-full bg-primary text-on-primary motion-safe:animate-[demo-pop_300ms_ease-out]">
      <Check className="size-3" strokeWidth={3} aria-hidden="true" />
    </span>
  );
}
