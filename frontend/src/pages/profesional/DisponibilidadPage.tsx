import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';
import { Trash2 } from 'lucide-react';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Alerta, inputClass } from '@/components/ui/Alerta';
import { errorDetail } from '@/components/turnos/errorDetail';
import { cn } from '@/utils/cn';
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

const hhmm = (t: string | null | undefined) => (t ? t.slice(0, 5) : '');

function semanaVacia(): Record<DiaSemana, FilaDia> {
  return Object.fromEntries(DIAS.map((d) => [d.id, { atiende: false, desde: '09:00', hasta: '18:00' }])) as Record<DiaSemana, FilaDia>;
}

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

  if (loading) return <p className="text-sm text-gray-500">Cargando…</p>;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Disponibilidad</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">Tus días y horarios de atención</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Semana habitual</CardTitle>
          <CardDescription>Un horario por día. Se repite todas las semanas.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={guardarSemana} className="space-y-3">
            {DIAS.map((d) => {
              const fila = semana[d.id];
              return (
                <div key={d.id} className="flex flex-wrap items-center gap-x-4 gap-y-2">
                  <label className="flex w-32 items-center gap-2 text-sm font-medium text-gray-900 dark:text-gray-100">
                    <input
                      type="checkbox"
                      checked={fila.atiende}
                      onChange={(e) => setDia(d.id, { atiende: e.target.checked })}
                      className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    {d.label}
                  </label>
                  {fila.atiende ? (
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <input type="time" aria-label={`${d.label} desde`} value={fila.desde} onChange={(e) => setDia(d.id, { desde: e.target.value })} className={inputClass} required />
                      a
                      <input type="time" aria-label={`${d.label} hasta`} value={fila.hasta} onChange={(e) => setDia(d.id, { hasta: e.target.value })} className={inputClass} required />
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400">No atiende</span>
                  )}
                </div>
              );
            })}
            {semanaError && <Alerta tipo="error">{semanaError}</Alerta>}
            {semanaOk && <Alerta tipo="ok">{semanaOk}</Alerta>}
            <div className="flex justify-end">
              <Button type="submit" loading={savingSemana}>Guardar semana</Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Excepciones</CardTitle>
          <CardDescription>Días cerrados u horarios distintos (feriados, vacaciones). Tienen prioridad sobre la semana.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {excepciones.length === 0 ? (
            <p className="text-sm text-gray-500">No tenés excepciones próximas.</p>
          ) : (
            <ul className="divide-y divide-gray-200 dark:divide-gray-700">
              {excepciones.map((x) => (
                <li key={x.id} className="flex flex-wrap items-center gap-3 py-2 text-sm">
                  <span className="w-36 font-medium capitalize text-gray-900 dark:text-white">
                    {format(parseISO(x.fecha), 'EEE d MMM yyyy', { locale: es })}
                  </span>
                  <span className={cn('flex-1', x.tipo === 'CERRADO' ? 'text-red-600 dark:text-red-400' : 'text-gray-700 dark:text-gray-300')}>
                    {x.tipo === 'CERRADO' ? 'Cerrado' : `${hhmm(x.hora_inicio)} a ${hhmm(x.hora_fin)}`}
                    {x.motivo && <span className="text-gray-500 dark:text-gray-400"> · {x.motivo}</span>}
                  </span>
                  <Button variant="ghost" size="sm" onClick={() => eliminarExcepcion(x.id)} aria-label={`Eliminar excepción del ${x.fecha}`}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </li>
              ))}
            </ul>
          )}

          <form onSubmit={agregarExcepcion} className="space-y-3 rounded-lg border border-gray-200 p-3 dark:border-gray-700">
            <p className="text-sm font-medium text-gray-900 dark:text-white">Agregar excepción</p>
            <div className="flex flex-wrap items-center gap-2">
              <input type="date" aria-label="Fecha" min={hoy} value={nueva.fecha} onChange={(e) => setNueva({ ...nueva, fecha: e.target.value })} className={inputClass} required />
              <select aria-label="Tipo" value={nueva.tipo} onChange={(e) => setNueva({ ...nueva, tipo: e.target.value as ExcepcionCreate['tipo'] })} className={inputClass}>
                <option value="CERRADO">Cerrado</option>
                <option value="HORARIO_ESPECIAL">Horario especial</option>
              </select>
              {nueva.tipo === 'HORARIO_ESPECIAL' && (
                <span className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <input type="time" aria-label="Desde" value={nueva.hora_inicio} onChange={(e) => setNueva({ ...nueva, hora_inicio: e.target.value })} className={inputClass} required />
                  a
                  <input type="time" aria-label="Hasta" value={nueva.hora_fin} onChange={(e) => setNueva({ ...nueva, hora_fin: e.target.value })} className={inputClass} required />
                </span>
              )}
            </div>
            <input
              type="text"
              aria-label="Motivo"
              placeholder="Motivo (opcional), ej. Feriado"
              maxLength={200}
              value={nueva.motivo}
              onChange={(e) => setNueva({ ...nueva, motivo: e.target.value })}
              className={`${inputClass} w-full`}
            />
            {excError && <Alerta tipo="error">{excError}</Alerta>}
            <div className="flex justify-end">
              <Button type="submit" variant="secondary" loading={savingExc}>Agregar</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
