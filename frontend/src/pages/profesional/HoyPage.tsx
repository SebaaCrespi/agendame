import { Fragment, useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { CalendarCheck, CalendarDays, CheckCheck, Clock, Hourglass } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';
import { Button, buttonClass } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Alerta } from '@/components/ui/Alerta';
import { EmptyState, PageHeader, Spinner, Stat } from '@/components/ui/misc';
import { EstadoBadge } from '@/components/turnos/EstadoBadge';
import { TurnoDetallePanel, accionesDisponibles } from '@/components/turnos/TurnoDetallePanel';
import { ACCION_LABEL, ES_CANCELADO } from '@/components/turnos/estado';
import { errorDetail } from '@/components/turnos/errorDetail';
import { cn } from '@/utils/cn';
import { capitalizar, fmt } from '@/utils/formato';
import { formatHora, minutosDelDia, parseHoraNegocio } from '@/utils/horaNegocio';
import type { Turno, TurnoEstado } from '@/types';

/** Etiquetas cortas para los botones de la lista. */
const ACCION_CORTA: Partial<Record<TurnoEstado, string>> = {
  CONFIRMADO: 'Confirmar',
  EN_CURSO: 'Iniciar',
  FINALIZADO: 'Finalizar',
  NO_ASISTIO: 'Ausente',
};

/** Agenda del día del profesional, con acciones rápidas de estado. */
export function ProfesionalHoyPage() {
  const { user } = useAuth();
  const [turnos, setTurnos] = useState<Turno[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Turno | null>(null);
  const [guardando, setGuardando] = useState<string | null>(null);
  const [ahora, setAhora] = useState(() => new Date());

  const cargar = useCallback(async () => {
    const hoy = format(new Date(), 'yyyy-MM-dd');
    try {
      const data = await api.getMisTurnosProfesional({ desde: hoy, hasta: hoy, page: 1, size: 100 });
      setTurnos([...data.items].sort((a, b) => a.fecha_inicio.localeCompare(b.fecha_inicio)));
      setError(null);
    } catch {
      setError('No se pudieron cargar los turnos de hoy');
      setTurnos([]);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  // La línea de "ahora" y las acciones dependen de la hora
  useEffect(() => {
    const t = setInterval(() => setAhora(new Date()), 60_000);
    return () => clearInterval(t);
  }, []);

  const actualizar = (t: Turno) => {
    setTurnos((prev) => prev?.map((x) => (x.id === t.id ? t : x)) ?? null);
    setSelected((s) => (s?.id === t.id ? t : s));
    // Reasignado a otro día: sale de la lista
    if (!t.fecha_inicio.startsWith(format(new Date(), 'yyyy-MM-dd'))) void cargar();
  };

  const cambiarEstado = async (t: Turno, destino: TurnoEstado) => {
    setGuardando(`${t.id}-${destino}`);
    setError(null);
    try {
      actualizar(await api.cambiarEstadoTurno(t.id, destino));
    } catch (err) {
      setError(errorDetail(err, 'No se pudo cambiar el estado'));
    } finally {
      setGuardando(null);
    }
  };

  const activos = (turnos ?? []).filter((t) => !ES_CANCELADO(t.estado));
  const finalizados = activos.filter((t) => t.estado === 'FINALIZADO').length;
  const pendientes = activos.filter((t) => t.estado === 'PENDIENTE').length;
  const minAhora = ahora.getHours() * 60 + ahora.getMinutes();
  const proximo = activos.find((t) => minutosDelDia(t.fecha_inicio) >= minAhora && (t.estado === 'CONFIRMADO' || t.estado === 'PENDIENTE'));
  // Índice del primer turno que empieza después de ahora: ahí va la línea roja
  const idxAhora = (turnos ?? []).findIndex((t) => minutosDelDia(t.fecha_inicio) > minAhora);

  return (
    <>
      <PageHeader
        title={`Hola, ${user?.nombre.split(' ')[0] ?? ''}`}
        description={`${capitalizar(fmt(ahora, "EEEE d 'de' MMMM"))} · ${activos.length} ${activos.length === 1 ? 'turno' : 'turnos'} hoy`}
        actions={
          <Link to="/profesional/agenda" className={buttonClass('outline')}>
            <CalendarDays /> Agenda semanal
          </Link>
        }
      />

      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Turnos hoy" value={turnos ? activos.length : '—'} icon={CalendarCheck} />
        <Stat label="Atendidos" value={turnos ? finalizados : '—'} icon={CheckCheck} />
        <Stat label="Por confirmar" value={turnos ? pendientes : '—'} icon={Hourglass} />
        <Stat label="Próximo" value={proximo ? formatHora(proximo.fecha_inicio) : '—'} hint={proximo?.cliente_nombre} icon={Clock} />
      </div>

      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}

      <div className="grid items-start gap-6 lg:grid-cols-[1fr_340px]">
        <Card padding="none" className="overflow-hidden">
          {turnos === null ? (
            <Spinner />
          ) : turnos.length === 0 ? (
            <EmptyState icon={CalendarCheck} title="No tenés turnos hoy" description="Cuando un cliente reserve para hoy, lo vas a ver acá." />
          ) : (
            <ol>
              {turnos.map((t, i) => {
                const enCurso = t.estado === 'EN_CURSO';
                const pasado = parseHoraNegocio(t.fecha_fin) <= ahora && !enCurso;
                const cancelado = ES_CANCELADO(t.estado);
                const acciones = accionesDisponibles(t, ahora);
                const duracion = minutosDelDia(t.fecha_fin) - minutosDelDia(t.fecha_inicio);
                return (
                  <Fragment key={t.id}>
                    {i === idxAhora && <LineaAhora hora={fmt(ahora, 'HH:mm')} />}
                    <li
                      className={cn(
                        'border-l-[3px] border-transparent transition-colors',
                        i > 0 && i !== idxAhora && 'border-t border-t-line',
                        enCurso && 'border-l-primary bg-primary-soft',
                        selected?.id === t.id && !enCurso && 'bg-surface-2'
                      )}
                    >
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-3 px-5 py-4">
                        <button
                          type="button"
                          onClick={() => setSelected(t)}
                          className={cn('flex min-w-0 flex-1 items-center gap-4 text-left', (pasado || cancelado) && 'opacity-60')}
                        >
                          <div className="w-14 shrink-0">
                            <p className="font-semibold text-fg tabular">{formatHora(t.fecha_inicio)}</p>
                            <p className="text-xs text-muted">{duracion} min</p>
                          </div>
                          <div className="min-w-0">
                            <p className={cn('truncate font-medium text-fg', cancelado && 'line-through')}>{t.cliente_nombre}</p>
                            <p className="truncate text-[13px] text-muted">{t.servicio_nombre}</p>
                          </div>
                        </button>
                        <div className="flex items-center gap-2 max-sm:w-full max-sm:pl-[4.5rem]">
                          <EstadoBadge estado={t.estado} />
                          {acciones.map((destino) => (
                            <Button
                              key={destino}
                              size="sm"
                              variant={destino === 'NO_ASISTIO' ? 'ghost' : enCurso || destino === 'CONFIRMADO' ? 'primary' : 'outline'}
                              title={ACCION_LABEL[destino]}
                              loading={guardando === `${t.id}-${destino}`}
                              disabled={guardando !== null}
                              onClick={() => cambiarEstado(t, destino)}
                            >
                              {ACCION_CORTA[destino]}
                            </Button>
                          ))}
                        </div>
                      </div>
                    </li>
                  </Fragment>
                );
              })}
              {idxAhora === -1 && <LineaAhora hora={fmt(ahora, 'HH:mm')} />}
            </ol>
          )}
        </Card>

        <div className="hidden lg:block">
          {selected ? (
            <TurnoDetallePanel key={selected.id} turno={selected} onClose={() => setSelected(null)} onUpdated={actualizar} />
          ) : (
            <div className="rounded-xl border border-dashed border-line-strong px-6 py-10 text-center text-[13px] text-muted">
              Elegí un turno para ver el detalle, agregar notas, reasignarlo o cancelarlo.
            </div>
          )}
        </div>
      </div>

      {/* En mobile el detalle va debajo de la lista */}
      {selected && (
        <div className="mt-6 lg:hidden">
          <TurnoDetallePanel key={selected.id} turno={selected} onClose={() => setSelected(null)} onUpdated={actualizar} />
        </div>
      )}
    </>
  );
}

function LineaAhora({ hora }: { hora: string }) {
  return (
    <li className="flex items-center gap-2 px-5 py-1" aria-label={`Ahora, ${hora}`}>
      <span className="text-xs font-semibold text-danger tabular">{hora}</span>
      <span className="h-px flex-1 bg-danger" aria-hidden="true" />
    </li>
  );
}
