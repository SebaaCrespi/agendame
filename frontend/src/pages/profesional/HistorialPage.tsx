import { useCallback, useEffect, useState } from 'react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { AlertCircle } from 'lucide-react';
import { api } from '@/services/api';
import { Paginacion } from '@/components/ui/Paginacion';
import { TurnoDetallePanel } from '@/components/turnos/TurnoDetallePanel';
import { ESTADO_COLOR, ESTADO_LABEL, GRUPOS_ESTADO, estadosDelGrupo, type GrupoEstado } from '@/components/turnos/estado';
import { cn } from '@/utils/cn';
import { formatHora, parseHoraNegocio } from '@/utils/horaNegocio';
import type { MomentoTurno, Servicio, Turno } from '@/types';

const POR_PAGINA = 20;

const inputClass =
  'rounded-md border border-gray-300 bg-white p-2 text-sm text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100';

/** Pasado y todavía pendiente o confirmado: nadie lo marcó finalizado ni ausente. */
function sinCerrar(turno: Turno, ahora: Date): boolean {
  return (
    (turno.estado === 'PENDIENTE' || turno.estado === 'CONFIRMADO') &&
    parseHoraNegocio(turno.fecha_fin) <= ahora
  );
}

/** Historial del proveedor (CU-09): turnos de cualquier rango, paginados. */
export function ProfesionalHistorialPage() {
  const [momento, setMomento] = useState<MomentoTurno | ''>('pasados');
  const [grupo, setGrupo] = useState<GrupoEstado>('todos');
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [servicioId, setServicioId] = useState<number | ''>('');
  const [cliente, setCliente] = useState('');
  const [clienteBuscado, setClienteBuscado] = useState('');
  const [page, setPage] = useState(1);

  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [servicios, setServicios] = useState<Servicio[]>([]);
  const [selected, setSelected] = useState<Turno | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ahora, setAhora] = useState(() => new Date());

  useEffect(() => {
    api.getMisServicios().then(setServicios).catch(() => setServicios([]));
  }, []);

  // Debounce de la búsqueda por cliente
  useEffect(() => {
    const t = setTimeout(() => {
      setClienteBuscado(cliente.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(t);
  }, [cliente]);

  const cargar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getMisTurnosProfesional({
        ...(momento && { momento }),
        estado: estadosDelGrupo(grupo),
        ...(desde && { desde }),
        ...(hasta && { hasta }),
        ...(servicioId && { servicio_id: servicioId }),
        ...(clienteBuscado && { cliente: clienteBuscado }),
        page,
        size: POR_PAGINA,
      });
      setTurnos(data.items);
      setPages(data.pages);
      setTotal(data.total);
      setAhora(new Date());
    } catch {
      setError('No se pudo cargar el historial');
    } finally {
      setLoading(false);
    }
  }, [momento, grupo, desde, hasta, servicioId, clienteBuscado, page]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  // Cualquier cambio de filtro vuelve a la primera página
  const filtrar = <T,>(set: (v: T) => void) => (v: T) => {
    set(v);
    setPage(1);
  };

  const onUpdated = (actualizado: Turno) => {
    const anterior = turnos.find((t) => t.id === actualizado.id);
    setTurnos((prev) => prev.map((t) => (t.id === actualizado.id ? actualizado : t)));
    setSelected(actualizado);
    // Cambió de estado o de fecha: puede haber salido de los filtros
    if (anterior && (anterior.estado !== actualizado.estado || anterior.fecha_inicio !== actualizado.fecha_inicio)) {
      void cargar();
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Historial</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">Todos tus turnos, de cualquier fecha</p>
      </div>

      {/* Filtros */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <select aria-label="Momento" value={momento} onChange={(e) => filtrar(setMomento)(e.target.value as MomentoTurno | '')} className={inputClass}>
          <option value="pasados">Pasados</option>
          <option value="proximos">Próximos</option>
          <option value="">Todos</option>
        </select>
        <select aria-label="Filtrar por estado" value={grupo} onChange={(e) => filtrar(setGrupo)(e.target.value as GrupoEstado)} className={inputClass}>
          {(Object.keys(GRUPOS_ESTADO) as GrupoEstado[]).map((g) => (
            <option key={g} value={g}>{g === 'todos' ? 'Todos los estados' : GRUPOS_ESTADO[g].label}</option>
          ))}
        </select>
        <select
          aria-label="Filtrar por servicio"
          value={servicioId}
          onChange={(e) => filtrar(setServicioId)(e.target.value ? Number(e.target.value) : '')}
          className={inputClass}
        >
          <option value="">Todos los servicios</option>
          {servicios.map((s) => (
            <option key={s.id} value={s.id}>{s.nombre}</option>
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
        <input
          type="search"
          aria-label="Buscar cliente"
          placeholder="Buscar cliente…"
          value={cliente}
          onChange={(e) => setCliente(e.target.value)}
          className={inputClass}
        />
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
          <AlertCircle className="h-4 w-4" /> {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className={cn('min-w-0 transition-opacity', loading && 'opacity-50')}>
          <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">{total} {total === 1 ? 'turno' : 'turnos'}</p>
          {!loading && turnos.length === 0 ? (
            <p className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500 dark:border-gray-700">
              No hay turnos con estos filtros.
            </p>
          ) : (
            <ul className="divide-y divide-gray-200 overflow-hidden rounded-lg border border-gray-200 bg-white dark:divide-gray-700 dark:border-gray-700 dark:bg-gray-900">
              {turnos.map((turno) => {
                const pendienteDeCierre = sinCerrar(turno, ahora);
                return (
                  <li key={turno.id}>
                    <button
                      type="button"
                      onClick={() => setSelected(turno)}
                      aria-current={selected?.id === turno.id}
                      className={cn(
                        'flex w-full flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-800',
                        selected?.id === turno.id && 'bg-indigo-50 dark:bg-indigo-900/20'
                      )}
                    >
                      <span className="w-28 shrink-0 font-medium capitalize text-gray-900 dark:text-white">
                        {format(parseHoraNegocio(turno.fecha_inicio), 'EEE d MMM', { locale: es })}
                      </span>
                      <span className="w-24 shrink-0 text-gray-500 dark:text-gray-400">
                        {formatHora(turno.fecha_inicio)} – {formatHora(turno.fecha_fin)}
                      </span>
                      <span className="w-full min-w-0 truncate text-gray-900 sm:w-auto sm:flex-1 dark:text-gray-100">
                        {turno.cliente_nombre} · <span className="text-gray-500 dark:text-gray-400">{turno.servicio_nombre}</span>
                      </span>
                      <span className="flex shrink-0 gap-1">
                        {pendienteDeCierre && (
                          <span className="rounded border border-amber-300 bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800 dark:border-amber-700 dark:bg-amber-900/30 dark:text-amber-200">
                            Sin cerrar
                          </span>
                        )}
                        <span className={cn('rounded border px-2 py-0.5 text-xs font-medium', ESTADO_COLOR[turno.estado])}>
                          {ESTADO_LABEL[turno.estado]}
                        </span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
          <Paginacion page={page} pages={pages} onChange={setPage} />
        </div>

        <div>
          {selected ? (
            <TurnoDetallePanel key={selected.id} turno={selected} onClose={() => setSelected(null)} onUpdated={onUpdated} />
          ) : (
            <p className="rounded-lg border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500 dark:border-gray-700">
              Elegí un turno para ver el detalle
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
