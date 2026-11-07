import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CalendarDays, CalendarPlus, Clock, MessageCircle, UserRound } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';
import { buttonClass } from '@/components/ui/Button';
import { Card, CardSection } from '@/components/ui/Card';
import { EmptyState, PageHeader, Skeleton } from '@/components/ui/misc';
import { Alerta } from '@/components/ui/Alerta';
import { EstadoBadge } from '@/components/turnos/EstadoBadge';
import { TurnoClienteItem } from '@/components/turnos/TurnoClienteItem';
import { EVENTO_ABRIR_ASISTENTE } from '@/components/chat/ChatWidget';
import { useTurnosCambiaron } from '@/hooks/useTurnosCambiaron';
import { capitalizar, fmt } from '@/utils/formato';
import { formatHora, parseHoraNegocio } from '@/utils/horaNegocio';
import type { Turno } from '@/types';

function saludo(d: Date) {
  const h = d.getHours();
  return h < 12 ? 'Buen día' : h < 20 ? 'Buenas tardes' : 'Buenas noches';
}

/** Cuánto falta para el turno, en palabras. */
function cuantoFalta(inicio: Date, ahora: Date): string {
  const min = Math.round((inicio.getTime() - ahora.getTime()) / 60_000);
  if (min < 60) return `en ${Math.max(min, 0)} min`;
  const horas = Math.round(min / 60);
  if (horas < 24) return `en ${horas} h`;
  const dias = Math.round(horas / 24);
  return dias === 1 ? 'mañana' : `en ${dias} días`;
}

export function ClienteInicioPage() {
  const { user } = useAuth();
  const [turnos, setTurnos] = useState<Turno[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ahora] = useState(() => new Date());

  const cargar = useCallback(() => {
    api
      .getMisTurnos({ momento: 'proximos', estado: ['PENDIENTE', 'CONFIRMADO', 'EN_CURSO'], page: 1, size: 4 })
      .then((d) => {
        setTurnos(d.items);
        setError(null);
      })
      .catch(() => setError('No se pudieron cargar tus próximos turnos'));
  }, []);

  useEffect(cargar, [cargar]);
  useTurnosCambiaron(cargar);

  const [proximo, ...siguientes] = turnos ?? [];
  const nombre = user?.nombre.split(' ')[0] ?? '';

  return (
    <>
      <PageHeader title={`${saludo(ahora)}, ${nombre}`} description={capitalizar(fmt(ahora, "EEEE d 'de' MMMM"))} />

      {error && <Alerta tipo="error" className="mb-6">{error}</Alerta>}

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        {/* Próximo turno */}
        <Card padding="none" className="overflow-hidden">
          {turnos === null ? (
            <div className="space-y-3 p-6">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-7 w-2/3" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          ) : !proximo ? (
            <EmptyState
              icon={CalendarDays}
              title="No tenés turnos próximos"
              description="Elegí profesional, servicio y horario en tres pasos."
              action={
                <Link to="/cliente/reservar" className={buttonClass('primary')}>
                  <CalendarPlus /> Reservar turno
                </Link>
              }
            />
          ) : (
            <div className="p-6">
              <div className="flex items-center justify-between gap-3">
                <p className="text-[13px] font-medium text-primary">Tu próximo turno · {cuantoFalta(parseHoraNegocio(proximo.fecha_inicio), ahora)}</p>
                <EstadoBadge estado={proximo.estado} />
              </div>
              <p className="mt-3 text-2xl font-semibold tracking-tight text-fg">
                {capitalizar(fmt(parseHoraNegocio(proximo.fecha_inicio), "EEEE d 'de' MMMM"))}
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <Dato icon={Clock} label="Horario" valor={`${formatHora(proximo.fecha_inicio)} – ${formatHora(proximo.fecha_fin)}`} />
                <Dato icon={CalendarDays} label="Servicio" valor={proximo.servicio_nombre} />
                <Dato icon={UserRound} label="Profesional" valor={proximo.profesional_nombre} />
              </div>
              <Link to="/cliente/mis-turnos" className={buttonClass('outline', 'sm', 'mt-6')}>
                Ver o cancelar <ArrowRight />
              </Link>
            </div>
          )}
        </Card>

        {/* Accesos rápidos */}
        <div className="grid gap-3">
          <Acceso to="/cliente/reservar" icon={CalendarPlus} titulo="Reservar turno" texto="Elegí profesional, día y hora" destacado />
          <Acceso to="/cliente/mis-turnos" icon={CalendarDays} titulo="Mis turnos" texto="Próximos, pasados y cancelaciones" />
          <button
            type="button"
            onClick={() => window.dispatchEvent(new Event(EVENTO_ABRIR_ASISTENTE))}
            className="group flex items-center gap-4 rounded-xl border border-line bg-surface p-4 text-left transition-colors hover:border-line-strong"
          >
            <span className="flex size-10 items-center justify-center rounded-lg bg-surface-2 text-muted">
              <MessageCircle className="size-5" aria-hidden="true" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block font-medium text-fg">Preguntale al asistente</span>
              <span className="block text-[13px] text-muted">Reservá conversando</span>
            </span>
            <ArrowRight className="size-4 text-subtle transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
          </button>
        </div>
      </div>

      {siguientes.length > 0 && (
        <Card padding="none" className="mt-6">
          <CardSection
            title="Después"
            actions={
              <Link to="/cliente/mis-turnos" className="text-[13px] font-medium text-primary hover:underline">
                Ver todos
              </Link>
            }
          />
          <ul className="divide-y divide-line">
            {siguientes.map((t) => (
              <TurnoClienteItem key={t.id} turno={t} />
            ))}
          </ul>
        </Card>
      )}
    </>
  );
}

function Dato({ icon: Icon, label, valor }: { icon: typeof Clock; label: string; valor: string }) {
  return (
    <div className="rounded-lg bg-surface-2 px-3 py-2.5">
      <p className="flex items-center gap-1.5 text-xs text-muted">
        <Icon className="size-3.5" aria-hidden="true" /> {label}
      </p>
      <p className="mt-0.5 truncate font-medium text-fg">{valor}</p>
    </div>
  );
}

function Acceso({ to, icon: Icon, titulo, texto, destacado }: { to: string; icon: typeof Clock; titulo: string; texto: string; destacado?: boolean }) {
  return (
    <Link to={to} className="group flex items-center gap-4 rounded-xl border border-line bg-surface p-4 transition-colors hover:border-line-strong">
      <span className={destacado ? 'flex size-10 items-center justify-center rounded-lg bg-primary text-on-primary' : 'flex size-10 items-center justify-center rounded-lg bg-surface-2 text-muted'}>
        <Icon className="size-5" aria-hidden="true" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block font-medium text-fg">{titulo}</span>
        <span className="block text-[13px] text-muted">{texto}</span>
      </span>
      <ArrowRight className="size-4 text-subtle transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
    </Link>
  );
}
