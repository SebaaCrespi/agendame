import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { addDays, format, isBefore, isSameDay, parseISO, startOfDay, startOfWeek } from 'date-fns';
import { ArrowLeft, Check, CheckCircle2, ChevronLeft, ChevronRight, Clock, Search, ShieldCheck, Stethoscope, UserRound } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';
import { Button, buttonClass } from '@/components/ui/Button';
import { Card, CardSection } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Alerta } from '@/components/ui/Alerta';
import { Avatar, EmptyState, PageHeader, Skeleton, Spinner } from '@/components/ui/misc';
import { errorDetail, errorStatus } from '@/components/turnos/errorDetail';
import { cn } from '@/utils/cn';
import { capitalizar, fmt, formatPrecio, hhmm } from '@/utils/formato';
import { parseHoraNegocio } from '@/utils/horaNegocio';
import { destinoReserva } from '@/utils/destino';
import type { DisponibilidadResponse, ProfesionalPublic, SlotDisponible, Turno } from '@/types';

type Paso = 1 | 2 | 3 | 4;

const PASOS: { n: Paso; label: string }[] = [
  { n: 1, label: 'Profesional' },
  { n: 2, label: 'Servicio' },
  { n: 3, label: 'Fecha y hora' },
  { n: 4, label: 'Confirmar' },
];

const hoy = () => startOfDay(new Date());

/**
 * CU-04: reserva en cuatro pasos. Lo elegido vive en la URL
 * (?prof=&serv=&fecha=&hora=), así "atrás" del navegador vuelve al paso anterior.
 */
export function ReservarPage() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const retomar = params.get('retomar') === '1';
  const profId = Number(params.get('prof')) || null;
  const servId = Number(params.get('serv')) || null;
  const fechaParam = params.get('fecha');
  const hora = params.get('hora');
  const confirmar = params.get('paso') === 'confirmar';

  const [profesionales, setProfesionales] = useState<ProfesionalPublic[] | null>(null);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const [busqueda, setBusqueda] = useState('');
  const [disponibilidad, setDisponibilidad] = useState<DisponibilidadResponse | null>(null);
  const [cargandoSlots, setCargandoSlots] = useState(false);
  const [reservando, setReservando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reservado, setReservado] = useState<Turno | null>(null);

  useEffect(() => {
    api
      .getProfesionalesPublic()
      .then((data) => setProfesionales(data.filter((p) => p.activo)))
      .catch(() => setErrorCarga('No se pudieron cargar los profesionales'));
  }, []);

  const prof = profesionales?.find((p) => p.id === profId) ?? null;
  const serv = prof?.servicios.find((s) => s.id === servId) ?? null;
  const fecha = fechaParam ? parseISO(fechaParam) : hoy();
  const inicioSemana = startOfWeek(fecha, { weekStartsOn: 1 });
  const semanaKey = format(inicioSemana, 'yyyy-MM-dd');

  const paso: Paso = !prof ? 1 : !serv ? 2 : !hora || !confirmar ? 3 : 4;

  /** Cambia la URL; `push` agrega una entrada al historial (cambio de paso). */
  const ir = (cambios: Record<string, string | null>, push = true) => {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(cambios)) {
      if (v === null) next.delete(k);
      else next.set(k, v);
    }
    setError(null);
    setParams(next, { replace: !push });
  };

  const cargarSlots = useCallback(async () => {
    if (!profId || !servId) return;
    setCargandoSlots(true);
    try {
      const desde = parseISO(semanaKey);
      setDisponibilidad(
        await api.consultarDisponibilidad({
          desde: semanaKey,
          hasta: format(addDays(desde, 6), 'yyyy-MM-dd'),
          profesional_id: profId,
          servicio_id: servId,
        })
      );
    } catch (err) {
      setDisponibilidad(null);
      setError(errorDetail(err, 'No se pudo cargar la disponibilidad'));
    } finally {
      setCargandoSlots(false);
    }
  }, [profId, servId, semanaKey]);

  useEffect(() => {
    void cargarSlots();
  }, [cargarSlots]);

  // Cada paso empieza arriba de la página
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [paso]);

  const slotsPorFecha = disponibilidad?.profesionales[0]?.slots_por_fecha ?? {};
  const fechaKey = format(fecha, 'yyyy-MM-dd');

  // Sin día elegido: abrir en el primer día de la semana con horarios libres
  useEffect(() => {
    if (fechaParam || !disponibilidad) return;
    const porFecha = disponibilidad.profesionales[0]?.slots_por_fecha ?? {};
    const primero = Object.keys(porFecha)
      .sort()
      .find((k) => k >= format(hoy(), 'yyyy-MM-dd') && porFecha[k].some((s) => s.disponible));
    if (primero) {
      const next = new URLSearchParams(params);
      next.set('fecha', primero);
      setParams(next, { replace: true });
    }
  }, [disponibilidad, fechaParam, params, setParams]);
  const slotsDelDia = slotsPorFecha[fechaKey] ?? [];
  const slotElegido = slotsDelDia.find((s) => s.hora_inicio === hora) ?? null;

  const reservar = async () => {
    if (!prof || !serv || !hora) return;
    setReservando(true);
    setError(null);
    try {
      const turno = await api.crearReserva({ profesional_id: prof.id, servicio_id: serv.id, fecha: fechaKey, hora_inicio: hora });
      setReservado(turno);
    } catch (err) {
      setError(errorDetail(err, 'No se pudo reservar el turno'));
      // El horario se ocupó mientras elegía: volver a elegir con datos frescos
      if (errorStatus(err) === 409) {
        ir({ hora: null, paso: null });
        void cargarSlots();
        setError('Ese horario se acaba de ocupar. Elegí otro.');
      }
    } finally {
      setReservando(false);
    }
  };

  if (reservado && prof && serv) {
    return <Exito turno={reservado} profesional={prof} servicio={serv.nombre} onOtro={() => { setReservado(null); setParams({}); }} />;
  }

  return (
    <>
      <PageHeader
        title="Reservar turno"
        description={
          paso === 1 ? 'Elegí con quién querés atenderte.' : paso === 2 ? `Elegí el servicio con ${prof?.nombre}.` : paso === 3 ? 'Elegí día y horario.' : 'Revisá los datos y confirmá.'
        }
      />

      <Stepper paso={paso} onIr={(n) => {
        if (n === 1) ir({ prof: null, serv: null, hora: null, paso: null });
        if (n === 2) ir({ serv: null, hora: null, paso: null });
        if (n === 3) ir({ paso: null });
      }} />

      {errorCarga && <Alerta tipo="error" className="mb-4">{errorCarga}</Alerta>}
      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}
      {retomar && paso === 4 && !reservado && user?.rol === 'CLIENTE' && (
        <Alerta tipo="ok" className="mb-4">Listo, ya estás dentro. Revisá los datos y confirmá tu turno.</Alerta>
      )}
      {user && user.rol !== 'CLIENTE' && paso === 4 && (
        <Alerta tipo="aviso" className="mb-4">Solo las cuentas de cliente pueden reservar turnos.</Alerta>
      )}

      <div className="grid items-start gap-6 lg:grid-cols-[1fr_320px]">
        <div className="min-w-0">
          {paso === 1 && (
            <PasoProfesional
              profesionales={profesionales}
              busqueda={busqueda}
              onBusqueda={setBusqueda}
              onElegir={(p) => ir({ prof: String(p.id), serv: null, hora: null, paso: null })}
            />
          )}

          {paso === 2 && prof && (
            <Card padding="none">
              <CardSection title="Servicios" />
              {prof.servicios.length === 0 ? (
                <EmptyState icon={Stethoscope} title="Sin servicios disponibles" description="Este profesional todavía no ofrece servicios para reservar." />
              ) : (
                <ul className="divide-y divide-line">
                  {prof.servicios.map((s) => (
                    <li key={s.id}>
                      <button
                        type="button"
                        onClick={() => ir({ serv: String(s.id), hora: null, paso: null })}
                        className="group flex w-full items-center gap-4 px-5 py-4 text-left transition-colors hover:bg-surface-2"
                      >
                        <div className="min-w-0 flex-1">
                          <p className="font-medium text-fg">{s.nombre}</p>
                          {s.descripcion && <p className="mt-0.5 line-clamp-2 text-[13px] text-muted">{s.descripcion}</p>}
                          <p className="mt-1 flex items-center gap-1.5 text-[13px] text-muted">
                            <Clock className="size-3.5" aria-hidden="true" /> {s.duracion_min} min
                          </p>
                        </div>
                        <span className="font-semibold text-fg tabular">{formatPrecio(s.precio)}</span>
                        <ChevronRight className="size-4 text-subtle transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          )}

          {paso === 3 && prof && serv && (
            <Card padding="none">
              <CardSection
                title={capitalizar(fmt(inicioSemana, 'MMMM yyyy'))}
                actions={
                  <div className="flex gap-1.5">
                    <Button
                      variant="outline"
                      size="icon"
                      aria-label="Semana anterior"
                      disabled={!isBefore(hoy(), inicioSemana)}
                      onClick={() => {
                        const prev = addDays(inicioSemana, -7);
                        ir({ fecha: format(isBefore(prev, hoy()) ? hoy() : prev, 'yyyy-MM-dd'), hora: null }, false);
                      }}
                    >
                      <ChevronLeft />
                    </Button>
                    <Button variant="outline" size="icon" aria-label="Semana siguiente" onClick={() => ir({ fecha: format(addDays(inicioSemana, 7), 'yyyy-MM-dd'), hora: null }, false)}>
                      <ChevronRight />
                    </Button>
                  </div>
                }
              />
              <div className="grid grid-cols-7 gap-1.5 border-b border-line p-3 sm:gap-2 sm:p-4" role="radiogroup" aria-label="Día">
                {Array.from({ length: 7 }, (_, i) => addDays(inicioSemana, i)).map((dia) => {
                  const key = format(dia, 'yyyy-MM-dd');
                  const libres = (slotsPorFecha[key] ?? []).filter((s) => s.disponible).length;
                  const pasado = isBefore(dia, hoy());
                  const sel = isSameDay(dia, fecha);
                  return (
                    <button
                      key={key}
                      type="button"
                      role="radio"
                      aria-checked={sel}
                      disabled={pasado}
                      onClick={() => ir({ fecha: key, hora: null }, false)}
                      className={cn(
                        'flex flex-col items-center rounded-xl border py-2 transition-colors sm:py-2.5',
                        sel ? 'border-primary bg-primary-soft text-primary' : 'border-line bg-surface text-fg hover:border-line-strong',
                        pasado && 'cursor-not-allowed opacity-40'
                      )}
                    >
                      <span className={cn('text-[11px] font-medium uppercase', sel ? 'text-primary' : 'text-muted')}>{fmt(dia, 'EEEEEE')}</span>
                      <span className="text-lg font-semibold tabular">{fmt(dia, 'd')}</span>
                      <span className={cn('mt-0.5 size-1.5 rounded-full', !pasado && libres > 0 ? 'bg-success' : 'bg-transparent')} aria-hidden="true" />
                      <span className="sr-only">{pasado ? 'pasado' : `${libres} horarios libres`}</span>
                    </button>
                  );
                })}
              </div>
              <div className="p-4 sm:p-5">
                {cargandoSlots && !disponibilidad ? (
                  <Spinner />
                ) : (
                  <SlotsDelDia
                    slots={slotsDelDia}
                    seleccion={hora}
                    cargando={cargandoSlots}
                    onElegir={(s) => ir({ hora: s.hora_inicio }, false)}
                    dia={fecha}
                  />
                )}
              </div>
            </Card>
          )}

          {paso === 4 && prof && serv && (
            <Card>
              <div className="flex items-start gap-4">
                <Avatar nombre={`${prof.nombre} ${prof.apellido}`} src={prof.foto_url} size="lg" />
                <div className="min-w-0">
                  <p className="text-lg font-semibold text-fg">{serv.nombre}</p>
                  <p className="text-muted">con {prof.nombre} {prof.apellido}</p>
                </div>
              </div>
              <dl className="mt-6 grid gap-3 sm:grid-cols-2">
                <Item label="Fecha" valor={capitalizar(fmt(fecha, "EEEE d 'de' MMMM"))} />
                <Item label="Horario" valor={slotElegido ? `${hhmm(slotElegido.hora_inicio)} – ${hhmm(slotElegido.hora_fin)}` : hhmm(hora)} />
                <Item label="Duración" valor={`${serv.duracion_min} minutos`} />
                <Item label="Precio" valor={formatPrecio(serv.precio)} />
              </dl>
              <p className="mt-6 flex items-start gap-2 rounded-lg bg-surface-2 px-3.5 py-3 text-[13px] text-muted">
                <ShieldCheck className="mt-px size-4 shrink-0 text-success" aria-hidden="true" />
                Podés cancelar sin cargo hasta 2 horas antes desde «Mis turnos».
              </p>
            </Card>
          )}
        </div>

        <Resumen
          paso={paso}
          profesional={prof}
          servicio={serv}
          fecha={paso >= 3 ? fecha : null}
          slot={slotElegido}
          hora={hora}
          reservando={reservando}
          modo={!user ? 'visitante' : user.rol === 'CLIENTE' ? 'cliente' : 'sin-permiso'}
          destino={destinoReserva(params)}
          onContinuar={() => ir({ paso: 'confirmar' })}
          onConfirmar={reservar}
          onVolver={() => window.history.back()}
        />
      </div>
    </>
  );
}

function Stepper({ paso, onIr }: { paso: Paso; onIr: (n: Paso) => void }) {
  return (
    <ol className="mb-6 flex items-center gap-2 overflow-x-auto pb-1" aria-label="Pasos de la reserva">
      {PASOS.map(({ n, label }, i) => {
        const hecho = n < paso;
        const actual = n === paso;
        return (
          <li key={n} className="flex shrink-0 items-center gap-2">
            {i > 0 && <span className={cn('h-px w-6 sm:w-10', hecho || actual ? 'bg-primary' : 'bg-line')} aria-hidden="true" />}
            <button
              type="button"
              disabled={!hecho}
              onClick={() => onIr(n)}
              aria-current={actual ? 'step' : undefined}
              className={cn('flex items-center gap-2 rounded-md text-[13px] font-medium', hecho ? 'text-fg hover:text-primary' : actual ? 'text-fg' : 'text-subtle')}
            >
              <span
                className={cn(
                  'flex size-6 items-center justify-center rounded-full border text-xs tabular',
                  hecho && 'border-primary bg-primary text-on-primary',
                  actual && 'border-primary text-primary ring-4 ring-primary-soft',
                  !hecho && !actual && 'border-line'
                )}
              >
                {hecho ? <Check className="size-3.5" strokeWidth={3} /> : n}
              </span>
              <span className={cn(!actual && 'max-sm:hidden')}>{label}</span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}

function PasoProfesional({
  profesionales,
  busqueda,
  onBusqueda,
  onElegir,
}: {
  profesionales: ProfesionalPublic[] | null;
  busqueda: string;
  onBusqueda: (v: string) => void;
  onElegir: (p: ProfesionalPublic) => void;
}) {
  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    if (!profesionales || !q) return profesionales;
    return profesionales.filter(
      (p) => `${p.nombre} ${p.apellido}`.toLowerCase().includes(q) || p.servicios.some((s) => s.nombre.toLowerCase().includes(q))
    );
  }, [profesionales, busqueda]);

  return (
    <div className="space-y-4">
      <Input type="search" aria-label="Buscar profesional o servicio" placeholder="Buscar por nombre o servicio…" leftIcon={<Search />} value={busqueda} onChange={(e) => onBusqueda(e.target.value)} />
      {filtrados === null ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      ) : filtrados.length === 0 ? (
        <Card padding="none">
          <EmptyState icon={UserRound} title={busqueda ? 'Sin resultados' : 'No hay profesionales disponibles'} description={busqueda ? 'Probá con otro nombre o servicio.' : undefined} />
        </Card>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {filtrados.map((p) => {
            const desde = p.servicios.length ? Math.min(...p.servicios.map((s) => s.precio)) : null;
            return (
              <li key={p.id}>
                <button
                  type="button"
                  onClick={() => onElegir(p)}
                  className="flex h-full w-full items-start gap-3.5 rounded-xl border border-line bg-surface p-4 text-left transition-colors hover:border-primary focus-visible:ring-4 focus-visible:ring-ring"
                >
                  <Avatar nombre={`${p.nombre} ${p.apellido}`} src={p.foto_url} />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-fg">{p.nombre} {p.apellido}</p>
                    {p.bio && <p className="mt-0.5 line-clamp-2 text-[13px] text-muted">{p.bio}</p>}
                    <p className="mt-2 text-xs text-muted">
                      {p.servicios.length} {p.servicios.length === 1 ? 'servicio' : 'servicios'}
                      {desde !== null && ` · desde ${formatPrecio(desde)}`}
                    </p>
                  </div>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

function SlotsDelDia({ slots, seleccion, cargando, onElegir, dia }: { slots: SlotDisponible[]; seleccion: string | null; cargando: boolean; onElegir: (s: SlotDisponible) => void; dia: Date }) {
  const libres = slots.filter((s) => s.disponible).length;
  if (slots.length === 0 || libres === 0) {
    return (
      <EmptyState
        icon={Clock}
        title={slots.length === 0 ? 'No atiende este día' : 'Sin horarios libres'}
        description="Elegí otro día de la semana o pasá a la siguiente."
        className="py-8"
      />
    );
  }
  const manana = slots.filter((s) => s.hora_inicio < '13:00');
  const tarde = slots.filter((s) => s.hora_inicio >= '13:00');
  return (
    <div className={cn('space-y-5 transition-opacity', cargando && 'opacity-50')}>
      <p className="text-[13px] text-muted">
        {capitalizar(fmt(dia, "EEEE d 'de' MMMM"))} · {libres} {libres === 1 ? 'horario libre' : 'horarios libres'}
      </p>
      {[
        { titulo: 'Mañana', lista: manana },
        { titulo: 'Tarde', lista: tarde },
      ]
        .filter((g) => g.lista.length > 0)
        .map((g) => (
          <div key={g.titulo}>
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-subtle">{g.titulo}</p>
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-5 xl:grid-cols-6" role="radiogroup" aria-label={`Horarios de la ${g.titulo.toLowerCase()}`}>
              {g.lista.map((s) => {
                const sel = seleccion === s.hora_inicio;
                return (
                  <button
                    key={s.hora_inicio}
                    type="button"
                    role="radio"
                    aria-checked={sel}
                    disabled={!s.disponible}
                    onClick={() => onElegir(s)}
                    className={cn(
                      'h-10 rounded-lg text-sm font-medium tabular transition-colors',
                      sel && 'bg-primary text-on-primary',
                      !sel && s.disponible && 'border border-line bg-surface text-fg hover:border-primary hover:text-primary',
                      !s.disponible && 'cursor-not-allowed bg-surface-2 text-subtle line-through'
                    )}
                  >
                    {hhmm(s.hora_inicio)}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
    </div>
  );
}

function Resumen({
  paso,
  profesional,
  servicio,
  fecha,
  slot,
  hora,
  reservando,
  modo,
  destino,
  onContinuar,
  onConfirmar,
  onVolver,
}: {
  paso: Paso;
  profesional: ProfesionalPublic | null;
  servicio: ProfesionalPublic['servicios'][number] | null;
  fecha: Date | null;
  slot: SlotDisponible | null;
  hora: string | null;
  reservando: boolean;
  /** Visitante: al confirmar se le pide crear cuenta y vuelve a este paso. */
  modo: 'cliente' | 'visitante' | 'sin-permiso';
  destino: string;
  onContinuar: () => void;
  onConfirmar: () => void;
  onVolver: () => void;
}) {
  const filas: [string, string | null][] = [
    ['Profesional', profesional ? `${profesional.nombre} ${profesional.apellido}` : null],
    ['Servicio', servicio?.nombre ?? null],
    ['Duración', servicio ? `${servicio.duracion_min} min` : null],
    ['Fecha', fecha ? capitalizar(fmt(fecha, 'EEE d MMM')) : null],
    ['Horario', hora ? (slot ? `${hhmm(slot.hora_inicio)} – ${hhmm(slot.hora_fin)}` : hhmm(hora)) : null],
  ];
  return (
    <Card className="lg:sticky lg:top-8">
      <h2 className="text-[15px] font-semibold text-fg">Tu reserva</h2>
      <dl className="mt-3 divide-y divide-line text-[13px]">
        {filas.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-3 py-2.5">
            <dt className="text-muted">{k}</dt>
            <dd className={cn('text-right font-medium', v ? 'text-fg' : 'text-subtle')}>{v ?? '—'}</dd>
          </div>
        ))}
        <div className="flex justify-between gap-3 py-2.5">
          <dt className="text-muted">Precio</dt>
          <dd className="text-base font-semibold text-fg tabular">{servicio ? formatPrecio(servicio.precio) : '—'}</dd>
        </div>
      </dl>
      {paso === 3 && (
        <Button className="mt-4 w-full" size="lg" disabled={!hora} onClick={onContinuar}>
          Continuar
        </Button>
      )}
      {paso === 4 && modo === 'visitante' && (
        <div className="mt-4 space-y-2">
          <p className="rounded-lg bg-primary-soft px-3 py-2.5 text-[13px] text-primary">
            Para confirmar necesitás una cuenta. Te lleva un minuto y volvés acá con tu turno listo.
          </p>
          <Link to={`/register?next=${encodeURIComponent(destino)}`} className={buttonClass('primary', 'lg', 'w-full')}>
            Crear cuenta y reservar
          </Link>
          <Link to={`/login?next=${encodeURIComponent(destino)}`} className={buttonClass('outline', 'md', 'w-full')}>
            Ya tengo cuenta
          </Link>
          <Button variant="ghost" className="w-full" onClick={onVolver}>
            <ArrowLeft /> Cambiar horario
          </Button>
        </div>
      )}
      {paso === 4 && modo !== 'visitante' && (
        <div className="mt-4 space-y-2">
          <Button className="w-full" size="lg" loading={reservando} disabled={modo === 'sin-permiso'} onClick={onConfirmar}>
            Confirmar reserva
          </Button>
          <Button variant="ghost" className="w-full" onClick={onVolver} disabled={reservando}>
            <ArrowLeft /> Cambiar horario
          </Button>
        </div>
      )}
      {paso < 3 && <p className="mt-3 text-xs text-muted">Completá los pasos para ver los horarios.</p>}
    </Card>
  );
}

function Item({ label, valor }: { label: string; valor: string }) {
  return (
    <div className="rounded-lg border border-line px-3.5 py-3">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-0.5 font-medium text-fg">{valor}</dd>
    </div>
  );
}

function Exito({ turno, profesional, servicio, onOtro }: { turno: Turno; profesional: ProfesionalPublic; servicio: string; onOtro: () => void }) {
  return (
    <Card padding="lg" className="mx-auto mt-4 max-w-lg text-center">
      <span className="mx-auto flex size-14 items-center justify-center rounded-full bg-success-soft text-success">
        <CheckCircle2 className="size-7" aria-hidden="true" />
      </span>
      <h1 className="mt-5 text-2xl font-semibold tracking-tight text-fg">¡Turno reservado!</h1>
      <p className="mt-2 text-muted">
        {servicio} con {profesional.nombre} {profesional.apellido}
      </p>
      <p className="mt-1 font-medium text-fg">{capitalizar(fmt(parseHoraNegocio(turno.fecha_inicio), "EEEE d 'de' MMMM, HH:mm"))} h</p>
      <div className="mt-8 flex flex-col justify-center gap-2 sm:flex-row">
        <Link to="/cliente/mis-turnos" className={buttonClass('primary')}>
          Ver mis turnos
        </Link>
        <Button variant="outline" onClick={onOtro}>
          Reservar otro
        </Button>
      </div>
    </Card>
  );
}
