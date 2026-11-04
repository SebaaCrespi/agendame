import { useCallback, useEffect, useState } from 'react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { AlertCircle, Calendar, Clock, XCircle } from 'lucide-react';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Paginacion } from '@/components/ui/Paginacion';
import { cn } from '@/utils/cn';
import { formatHora, parseHoraNegocio } from '@/utils/horaNegocio';
import { CancelarDialog } from './CancelarDialog';
import { ESTADO_COLOR, ESTADO_LABEL, GRUPOS_ESTADO, estadosDelGrupo, type GrupoEstado } from './estado';
import type { MomentoTurno, Turno } from '@/types';

const POR_PAGINA = 10;
const CANCELACION_HORAS_ANTES = 2;

const inputClass =
  'rounded-md border border-gray-300 bg-white p-2 text-sm text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100';

/** El backend permite cancelar PENDIENTE/CONFIRMADO con más de 2 h de antelación. */
function puedeCancelar(turno: Turno, ahora: Date): boolean {
  if (turno.estado !== 'PENDIENTE' && turno.estado !== 'CONFIRMADO') return false;
  const horas = (parseHoraNegocio(turno.fecha_inicio).getTime() - ahora.getTime()) / 3_600_000;
  return horas > CANCELACION_HORAS_ANTES;
}

interface MisTurnosClienteProps {
  onReservar: () => void;
}

/** Historial del cliente (CU-09): próximos y pasados, filtros y cancelación (CU-08). */
export function MisTurnosCliente({ onReservar }: MisTurnosClienteProps) {
  const [momento, setMomento] = useState<MomentoTurno>('proximos');
  const [grupo, setGrupo] = useState<GrupoEstado>('todos');
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [page, setPage] = useState(1);

  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ahora, setAhora] = useState(() => new Date());
  const [turnoACancelar, setTurnoACancelar] = useState<Turno | null>(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getMisTurnos({
        momento,
        estado: estadosDelGrupo(grupo),
        ...(desde && { desde }),
        ...(hasta && { hasta }),
        page,
        size: POR_PAGINA,
      });
      setTurnos(data.items);
      setPages(data.pages);
      setTotal(data.total);
      setAhora(new Date());
    } catch {
      setError('No se pudieron cargar tus turnos');
    } finally {
      setLoading(false);
    }
  }, [momento, grupo, desde, hasta, page]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  // Cualquier cambio de filtro vuelve a la primera página
  const filtrar = <T,>(set: (v: T) => void) => (v: T) => {
    set(v);
    setPage(1);
  };

  return (
    <div className="space-y-4">
      {/* Próximos / Pasados */}
      <div className="flex gap-2" role="tablist" aria-label="Momento">
        {(['proximos', 'pasados'] as const).map((m) => (
          <button
            key={m}
            type="button"
            role="tab"
            aria-selected={momento === m}
            onClick={() => filtrar(setMomento)(m)}
            className={cn(
              'rounded-full px-4 py-1.5 text-sm font-medium transition-colors',
              momento === m
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
            )}
          >
            {m === 'proximos' ? 'Próximos' : 'Pasados'}
          </button>
        ))}
      </div>

      {/* Filtros */}
      <div className="grid gap-3 sm:grid-cols-3">
        <select
          aria-label="Filtrar por estado"
          value={grupo}
          onChange={(e) => filtrar(setGrupo)(e.target.value as GrupoEstado)}
          className={inputClass}
        >
          {(Object.keys(GRUPOS_ESTADO) as GrupoEstado[]).map((g) => (
            <option key={g} value={g}>{GRUPOS_ESTADO[g].label}</option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          Desde
          <input type="date" value={desde} max={hasta || undefined} onChange={(e) => filtrar(setDesde)(e.target.value)} className={cn(inputClass, 'flex-1')} />
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          Hasta
          <input type="date" value={hasta} min={desde || undefined} onChange={(e) => filtrar(setHasta)(e.target.value)} className={cn(inputClass, 'flex-1')} />
        </label>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
          <AlertCircle className="h-4 w-4" /> {error}
        </div>
      )}

      {loading && turnos.length === 0 ? (
        <div className="flex justify-center py-8">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
        </div>
      ) : turnos.length === 0 ? (
        <div className="py-12 text-center">
          <Calendar className="mx-auto mb-4 h-16 w-16 text-gray-300 dark:text-gray-600" />
          <h3 className="mb-2 text-lg font-medium text-gray-900 dark:text-white">
            {momento === 'proximos' ? 'No tenés turnos próximos' : 'No hay turnos pasados'}
          </h3>
          <p className="mb-4 text-gray-500 dark:text-gray-400">
            {grupo === 'todos' && !desde && !hasta ? 'Cuando reserves, aparecerán acá' : 'Probá con otros filtros'}
          </p>
          {momento === 'proximos' && (
            <Button onClick={onReservar}>Reservar un turno</Button>
          )}
        </div>
      ) : (
        <div className={cn('space-y-3 transition-opacity', loading && 'opacity-50')}>
          <p className="text-sm text-gray-500 dark:text-gray-400">{total} {total === 1 ? 'turno' : 'turnos'}</p>
          {turnos.map((turno) => {
            const inicio = parseHoraNegocio(turno.fecha_inicio);
            return (
              <div
                key={turno.id}
                className="flex flex-wrap items-start gap-4 rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900"
              >
                <div className="flex h-16 w-16 flex-shrink-0 flex-col items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
                  <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{format(inicio, 'd')}</span>
                  <span className="text-xs text-indigo-600 dark:text-indigo-400">{format(inicio, 'MMM', { locale: es })}</span>
                </div>
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h4 className="truncate font-medium text-gray-900 dark:text-white">{turno.profesional_nombre}</h4>
                    <span className={cn('rounded border px-2 py-0.5 text-xs font-medium', ESTADO_COLOR[turno.estado])}>
                      {ESTADO_LABEL[turno.estado]}
                    </span>
                  </div>
                  <p className="truncate text-sm text-gray-500 dark:text-gray-400">{turno.servicio_nombre}</p>
                  <p className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
                    <Clock className="h-4 w-4" />
                    <span>
                      <span className="capitalize">{format(inicio, 'EEEE', { locale: es })}</span>,{' '}
                      {formatHora(turno.fecha_inicio)} – {formatHora(turno.fecha_fin)}
                    </span>
                  </p>
                  {turno.motivo_cancelacion && (
                    <p className="text-sm text-gray-500 dark:text-gray-400">Motivo: {turno.motivo_cancelacion}</p>
                  )}
                  {turno.reasignado_desde && (
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Reasignado: antes era el {format(parseHoraNegocio(turno.reasignado_desde), "d MMM, HH:mm", { locale: es })}
                      {turno.motivo_reasignacion && ` (${turno.motivo_reasignacion})`}
                    </p>
                  )}
                </div>
                {puedeCancelar(turno, ahora) && (
                  // En mobile va en su propia línea para no recortar el nombre
                  <div className="flex w-full justify-end sm:w-auto">
                    <Button variant="outline" size="sm" onClick={() => setTurnoACancelar(turno)}>
                      <XCircle className="h-4 w-4" />
                      Cancelar
                    </Button>
                  </div>
                )}
              </div>
            );
          })}
          <Paginacion page={page} pages={pages} onChange={setPage} />
        </div>
      )}

      {turnoACancelar && (
        <CancelarDialog
          open
          resumen={`${format(parseHoraNegocio(turnoACancelar.fecha_inicio), "EEEE d MMM, HH:mm", { locale: es })} · ${turnoACancelar.servicio_nombre} con ${turnoACancelar.profesional_nombre}`}
          cancelar={(motivo) => api.cancelarTurnoCliente(turnoACancelar.id, motivo)}
          onClose={() => setTurnoACancelar(null)}
          onCancelado={() => {
            setTurnoACancelar(null);
            void cargar();
          }}
        />
      )}
    </div>
  );
}
