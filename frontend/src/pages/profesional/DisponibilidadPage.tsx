import { DateField } from '@/components/ui/DateField';
import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { format, parseISO } from 'date-fns';
import { CalendarOff, Trash2 } from 'lucide-react';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card, CardDescription, CardTitle } from '@/components/ui/Card';
import { Input, Select } from '@/components/ui/Input';
import { Alerta } from '@/components/ui/Alerta';
import { Spinner } from '@/components/ui/misc';
import { Badge } from '@/components/turnos/EstadoBadge';
import { errorDetail } from '@/components/turnos/errorDetail';
import { cn } from '@/utils/cn';
import { capitalizar, fmt, hhmm } from '@/utils/formato';
import type { DiaSemana, DisponibilidadCreate, ExcepcionCreate, ExcepcionDisponibilidad } from '@/types';

const DIAS: { id: DiaSemana; label: string }[] = [
  { id: 'LUNES', label: 'Lunes' },
  { id: 'MARTES', label: 'Martes' },
  { id: 'MIERCOLES', label: 'Miércoles' },
  { id: 'JUEVES', label: 'Jueves' },
  { id: 'VIERNES', label: 'Viernes' },
  { id: 'SABADO', label: 'Sábado' },
  { id: 'DOMINGO', label: 'Domingo' },
];

interface FilaDia {
  atiende: boolean;
  desde: string; // HH:MM
  hasta: string;
}

function semanaVacia(): Record<DiaSemana, FilaDia> {
  return Object.fromEntries(DIAS.map((d) => [d.id, { atiende: false, desde: '09:00', hasta: '18:00' }])) as Record<DiaSemana, FilaDia>;
}

const timeClass = 'h-9 w-[7.5rem]';

/** CU-02: grilla semanal y excepciones del proveedor. */
export function ProfesionalDisponibilidadPage() {
  const [hoy] = useState(() => format(new Date(), 'yyyy-MM-dd'));
  const [semana, setSemana] = useState<Record<DiaSemana, FilaDia>>(semanaVacia);
  const [excepciones, setExcepciones] = useState<ExcepcionDisponibilidad[]>([]);
  const [loading, setLoading] = useState(true);

  const [savingSemana, setSavingSemana] = useState(false);
  const [semanaError, setSemanaError] = useState<string | null>(null);
  const [semanaOk, setSemanaOk] = useState<string | null>(null);

  const [nueva, setNueva] = useState<ExcepcionCreate>({ fecha: '', tipo: 'CERRADO', hora_inicio: '10:00', hora_fin: '14:00', motivo: '' });
  const [savingExc, setSavingExc] = useState(false);
  const [excError, setExcError] = useState<string | null>(null);

  const cargarExcepciones = useCallback(async () => {
    const data = await api.getMisExcepciones(hoy);
    setExcepciones([...data].sort((a, b) => a.fecha.localeCompare(b.fecha)));
  }, [hoy]);

  useEffect(() => {
    Promise.all([api.getMiGrilla(), cargarExcepciones()])
      .then(([{ grilla }]) => {
        const s = semanaVacia();
        for (const d of grilla) {
          if (d.activo) s[d.dia_semana] = { atiende: true, desde: hhmm(d.hora_inicio), hasta: hhmm(d.hora_fin) };
        }
        setSemana(s);
      })
      .catch((err) => setSemanaError(errorDetail(err, 'No se pudo cargar tu disponibilidad')))
      .finally(() => setLoading(false));
  }, [cargarExcepciones]);

  const setDia = (dia: DiaSemana, cambio: Partial<FilaDia>) => {
    setSemana((s) => ({ ...s, [dia]: { ...s[dia], ...cambio } }));
    setSemanaOk(null);
  };

  const guardarSemana = async (e: FormEvent) => {
    e.preventDefault();
    const grilla: DisponibilidadCreate[] = DIAS.filter((d) => semana[d.id].atiende).map((d) => ({
      dia_semana: d.id,
      hora_inicio: semana[d.id].desde,
      hora_fin: semana[d.id].hasta,
    }));
    const invalido = DIAS.find((d) => semana[d.id].atiende && semana[d.id].hasta <= semana[d.id].desde);
    if (invalido) {
      setSemanaError(`${invalido.label}: el cierre tiene que ser después de la apertura`);
      return;
    }
    setSavingSemana(true);
    setSemanaError(null);
    try {
      await api.actualizarGrillaCompleta(grilla);
      setSemanaOk('Semana guardada');
    } catch (err) {
      setSemanaError(errorDetail(err, 'No se pudo guardar la semana'));
    } finally {
      setSavingSemana(false);
    }
  };

  const agregarExcepcion = async (e: FormEvent) => {
    e.preventDefault();
    const especial = nueva.tipo === 'HORARIO_ESPECIAL';
    setSavingExc(true);
    setExcError(null);
    try {
      await api.agregarExcepcion({
        fecha: nueva.fecha,
        tipo: nueva.tipo,
        ...(especial && { hora_inicio: nueva.hora_inicio, hora_fin: nueva.hora_fin }),
        ...(nueva.motivo?.trim() && { motivo: nueva.motivo.trim() }),
      });
      setNueva({ ...nueva, fecha: '', motivo: '' });
      await cargarExcepciones();
    } catch (err) {
      setExcError(errorDetail(err, 'No se pudo agregar la excepción'));
    } finally {
      setSavingExc(false);
    }
  };

  const eliminarExcepcion = async (id: number) => {
    setExcError(null);
    try {
      await api.eliminarExcepcion(id);
      await cargarExcepciones();
    } catch (err) {
      setExcError(errorDetail(err, 'No se pudo eliminar la excepción'));
    }
  };

  if (loading) return <Spinner />;

  return (
    <div className="grid max-w-5xl items-start gap-6 lg:grid-cols-[1.2fr_1fr]">
      <Card padding="none">
        <div className="border-b border-line px-5 py-4">
          <CardTitle>Semana habitual</CardTitle>
          <CardDescription>Un horario por día. Se repite todas las semanas.</CardDescription>
        </div>
        <form onSubmit={guardarSemana}>
          <ul className="divide-y divide-line">
            {DIAS.map((d) => {
              const fila = semana[d.id];
              return (
                <li key={d.id} className="flex min-h-[60px] flex-wrap items-center gap-x-4 gap-y-2 px-5 py-2.5">
                  <label className="flex w-32 cursor-pointer items-center gap-3 text-sm font-medium text-fg">
                    <Switch checked={fila.atiende} onChange={(v) => setDia(d.id, { atiende: v })} label={`Atiende ${d.label}`} />
                    {d.label}
                  </label>
                  {fila.atiende ? (
                    <div className="flex items-center gap-2 text-[13px] text-muted">
                      <Input type="time" aria-label={`${d.label} desde`} value={fila.desde} onChange={(e) => setDia(d.id, { desde: e.target.value })} className={timeClass} wrapperClassName="w-auto" required />
                      a
                      <Input type="time" aria-label={`${d.label} hasta`} value={fila.hasta} onChange={(e) => setDia(d.id, { hasta: e.target.value })} className={timeClass} wrapperClassName="w-auto" required />
                    </div>
                  ) : (
                    <span className="text-[13px] text-subtle">No atiende</span>
                  )}
                </li>
              );
            })}
          </ul>
          <div className="space-y-3 border-t border-line px-5 py-4">
            {semanaError && <Alerta tipo="error">{semanaError}</Alerta>}
            {semanaOk && <Alerta tipo="ok">{semanaOk}</Alerta>}
            <div className="flex justify-end">
              <Button type="submit" loading={savingSemana}>Guardar semana</Button>
            </div>
          </div>
        </form>
      </Card>

      <Card padding="none">
        <div className="border-b border-line px-5 py-4">
          <CardTitle>Excepciones</CardTitle>
          <CardDescription>Feriados, vacaciones u horarios distintos. Tienen prioridad sobre la semana.</CardDescription>
        </div>

        {excepciones.length === 0 ? (
          <p className="flex items-center gap-2 px-5 py-6 text-[13px] text-muted">
            <CalendarOff className="size-4" aria-hidden="true" /> No tenés excepciones próximas.
          </p>
        ) : (
          <ul className="divide-y divide-line">
            {excepciones.map((x) => (
              <li key={x.id} className="flex items-center gap-3 px-5 py-3">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-fg">{capitalizar(fmt(parseISO(x.fecha), "EEE d 'de' MMMM"))}</p>
                  <p className="flex flex-wrap items-center gap-2 text-[13px] text-muted">
                    {x.tipo === 'CERRADO' ? (
                      <Badge className="bg-danger-soft text-danger">Cerrado</Badge>
                    ) : (
                      <Badge className="bg-info-soft text-info">{hhmm(x.hora_inicio)} a {hhmm(x.hora_fin)}</Badge>
                    )}
                    {x.motivo}
                  </p>
                </div>
                <Button variant="ghost" size="icon" className="hover:text-danger" onClick={() => eliminarExcepcion(x.id)} aria-label={`Eliminar excepción del ${x.fecha}`}>
                  <Trash2 />
                </Button>
              </li>
            ))}
          </ul>
        )}

        <form onSubmit={agregarExcepcion} className="space-y-3 border-t border-line bg-canvas/50 px-5 py-4">
          <p className="text-[13px] font-medium text-fg">Agregar excepción</p>
          <div className="grid grid-cols-2 gap-2">
            <DateField aria-label="Fecha" min={hoy} value={nueva.fecha} onChange={(v) => setNueva({ ...nueva, fecha: v })} required />
            <Select aria-label="Tipo" value={nueva.tipo} onChange={(e) => setNueva({ ...nueva, tipo: e.target.value as ExcepcionCreate['tipo'] })}>
              <option value="CERRADO">Cerrado</option>
              <option value="HORARIO_ESPECIAL">Horario especial</option>
            </Select>
          </div>
          {nueva.tipo === 'HORARIO_ESPECIAL' && (
            <div className="flex items-center gap-2 text-[13px] text-muted">
              <Input type="time" aria-label="Desde" value={nueva.hora_inicio} onChange={(e) => setNueva({ ...nueva, hora_inicio: e.target.value })} required />
              a
              <Input type="time" aria-label="Hasta" value={nueva.hora_fin} onChange={(e) => setNueva({ ...nueva, hora_fin: e.target.value })} required />
            </div>
          )}
          <Input aria-label="Motivo" placeholder="Motivo (opcional), ej. Feriado" maxLength={200} value={nueva.motivo} onChange={(e) => setNueva({ ...nueva, motivo: e.target.value })} />
          {excError && <Alerta tipo="error">{excError}</Alerta>}
          <div className="flex justify-end">
            <Button type="submit" variant="secondary" loading={savingExc}>Agregar</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

function Switch({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={cn('relative h-5 w-9 shrink-0 rounded-full transition-colors', checked ? 'bg-primary' : 'bg-line-strong')}
    >
      <span className={cn('absolute left-0 top-0.5 size-4 rounded-full bg-white shadow-sm transition-transform', checked ? 'translate-x-[18px]' : 'translate-x-0.5')} />
    </button>
  );
}
