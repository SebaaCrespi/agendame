import { useCallback, useEffect, useState } from 'react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { api } from '@/services/api';
import { Paginacion } from '@/components/ui/Paginacion';
import { Alerta, inputClass } from '@/components/ui/Alerta';
import { ESTADO_COLOR, ESTADO_LABEL, ESTADOS } from '@/components/turnos/estado';
import { errorDetail } from '@/components/turnos/errorDetail';
import { cn } from '@/utils/cn';
import { formatHora, parseHoraNegocio } from '@/utils/horaNegocio';
import type { Profesional, Turno, TurnoEstado } from '@/types';

const POR_PAGINA = 20;

/** CU-10: turnos de todos los profesionales, solo lectura. */
export function AdminTurnosPage() {
  const [profesionalId, setProfesionalId] = useState<number | ''>('');
  const [estado, setEstado] = useState<TurnoEstado | ''>('');
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [page, setPage] = useState(1);

  const [profesionales, setProfesionales] = useState<Profesional[]>([]);
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getProfesionalesAdmin({ size: 100 })
      .then((d) => setProfesionales([...d.items].sort((a, b) => a.nombre.localeCompare(b.nombre))))
      .catch(() => setProfesionales([]));
  }, []);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getAllTurnosAdmin({
        page,
        size: POR_PAGINA,
        ...(profesionalId && { profesional_id: profesionalId }),
        ...(estado && { estado }),
        ...(desde && { desde }),
        ...(hasta && { hasta }),
      });
      setTurnos(data.items);
      setPages(data.pages);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(errorDetail(err, 'No se pudieron cargar los turnos'));
    } finally {
      setLoading(false);
    }
  }, [page, profesionalId, estado, desde, hasta]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const filtrar = <T,>(set: (v: T) => void) => (v: T) => {
    set(v);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Todos los turnos</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">Solo lectura. Cada profesional gestiona los suyos.</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <select aria-label="Profesional" value={profesionalId} onChange={(e) => filtrar(setProfesionalId)(e.target.value ? Number(e.target.value) : '')} className={inputClass}>
          <option value="">Todos los profesionales</option>
          {profesionales.map((p) => (
            <option key={p.id} value={p.id}>{p.nombre} {p.apellido}</option>
          ))}
        </select>
        <select aria-label="Estado" value={estado} onChange={(e) => filtrar(setEstado)(e.target.value as TurnoEstado | '')} className={inputClass}>
          <option value="">Todos los estados</option>
          {ESTADOS.map((e) => (
            <option key={e} value={e}>{ESTADO_LABEL[e]}</option>
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

      {error && <Alerta tipo="error">{error}</Alerta>}

      <div className={cn('transition-opacity', loading && 'opacity-50')}>
        <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">{total} {total === 1 ? 'turno' : 'turnos'}</p>
        {!loading && turnos.length === 0 ? (
          <p className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500 dark:border-gray-700">
            No hay turnos con estos filtros.
          </p>
        ) : (
          <ul className="divide-y divide-gray-200 overflow-hidden rounded-lg border border-gray-200 bg-white dark:divide-gray-700 dark:border-gray-700 dark:bg-gray-900">
            {turnos.map((t) => (
              <li key={t.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 text-sm">
                <span className="w-28 shrink-0 font-medium capitalize text-gray-900 dark:text-white">
                  {format(parseHoraNegocio(t.fecha_inicio), 'EEE d MMM', { locale: es })}
                </span>
                <span className="w-24 shrink-0 text-gray-500 dark:text-gray-400">
                  {formatHora(t.fecha_inicio)} – {formatHora(t.fecha_fin)}
                </span>
                <span className="w-full min-w-0 truncate text-gray-900 sm:w-auto sm:flex-1 dark:text-gray-100">
                  {t.profesional_nombre} · {t.cliente_nombre} · <span className="text-gray-500 dark:text-gray-400">{t.servicio_nombre}</span>
                </span>
                <span className={cn('shrink-0 rounded border px-2 py-0.5 text-xs font-medium', ESTADO_COLOR[t.estado])}>
                  {ESTADO_LABEL[t.estado]}
                </span>
              </li>
            ))}
          </ul>
        )}
        <Paginacion page={page} pages={pages} onChange={setPage} />
      </div>
    </div>
  );
}
