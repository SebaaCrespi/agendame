import { useCallback, useEffect, useState } from 'react';
import { History, Search } from 'lucide-react';
import { api } from '@/services/api';
import { Card } from '@/components/ui/Card';
import { Input, Select } from '@/components/ui/Input';
import { Paginacion } from '@/components/ui/Paginacion';
import { Alerta } from '@/components/ui/Alerta';
import { EmptyState, PageHeader, Segmented, Spinner } from '@/components/ui/misc';
import { TurnoDetallePanel } from '@/components/turnos/TurnoDetallePanel';
import { Badge, EstadoBadge } from '@/components/turnos/EstadoBadge';
import { GRUPOS_ESTADO, estadosDelGrupo, type GrupoEstado } from '@/components/turnos/estado';
import { cn } from '@/utils/cn';
import { capitalizar, fmt, plural } from '@/utils/formato';
import { formatHora, parseHoraNegocio } from '@/utils/horaNegocio';
import type { MomentoTurno, Servicio, Turno } from '@/types';

const POR_PAGINA = 20;

/** Pasado y todavía pendiente o confirmado: nadie lo marcó finalizado ni ausente. */
function sinCerrar(turno: Turno, ahora: Date): boolean {
  return (turno.estado === 'PENDIENTE' || turno.estado === 'CONFIRMADO') && parseHoraNegocio(turno.fecha_fin) <= ahora;
}

type Momento = MomentoTurno | 'todos';

/** CU-09: historial del proveedor, cualquier rango, paginado. */
export function ProfesionalHistorialPage() {
  const [momento, setMomento] = useState<Momento>('pasados');
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
        ...(momento !== 'todos' && { momento }),
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
    if (anterior && (anterior.estado !== actualizado.estado || anterior.fecha_inicio !== actualizado.fecha_inicio)) void cargar();
  };

  return (
    <>
      <PageHeader title="Historial" description="Todos tus turnos, de cualquier fecha." />

      <div className="mb-4 space-y-3">
        <Segmented
          label="Momento"
          value={momento}
          onChange={filtrar(setMomento)}
          options={[
            { value: 'pasados', label: 'Pasados' },
            { value: 'proximos', label: 'Próximos' },
            { value: 'todos', label: 'Todos' },
          ]}
        />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Input type="search" aria-label="Buscar cliente" placeholder="Buscar cliente…" leftIcon={<Search />} value={cliente} onChange={(e) => setCliente(e.target.value)} wrapperClassName="lg:col-span-1" />
          <Select aria-label="Filtrar por estado" value={grupo} onChange={(e) => filtrar(setGrupo)(e.target.value as GrupoEstado)}>
            {(Object.keys(GRUPOS_ESTADO) as GrupoEstado[]).map((g) => (
              <option key={g} value={g}>{g === 'todos' ? 'Todos los estados' : GRUPOS_ESTADO[g].label}</option>
            ))}
          </Select>
          <Select aria-label="Filtrar por servicio" value={servicioId} onChange={(e) => filtrar(setServicioId)(e.target.value ? Number(e.target.value) : '')}>
            <option value="">Todos los servicios</option>
            {servicios.map((s) => (
              <option key={s.id} value={s.id}>{s.nombre}</option>
            ))}
          </Select>
          <Input type="date" aria-label="Desde" title="Desde" value={desde} max={hasta || undefined} onChange={(e) => filtrar(setDesde)(e.target.value)} />
          <Input type="date" aria-label="Hasta" title="Hasta" value={hasta} min={desde || undefined} onChange={(e) => filtrar(setHasta)(e.target.value)} />
        </div>
      </div>

      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}

      <div className="grid items-start gap-6 lg:grid-cols-[1fr_320px]">
        <Card padding="none" className="min-w-0 overflow-hidden">
          {loading && turnos.length === 0 ? (
            <Spinner />
          ) : turnos.length === 0 ? (
            <EmptyState icon={History} title="Sin turnos" description="No hay turnos con estos filtros." />
          ) : (
            <div className={cn('transition-opacity', loading && 'opacity-50')}>
              <p className="border-b border-line px-5 py-3 text-[13px] text-muted">{plural(total, 'turno')}</p>
              <ul className="divide-y divide-line">
                {turnos.map((t) => {
                  const inicio = parseHoraNegocio(t.fecha_inicio);
                  return (
                    <li key={t.id}>
                      <button
                        type="button"
                        onClick={() => setSelected(t)}
                        aria-current={selected?.id === t.id}
                        className={cn(
                          'flex w-full flex-wrap items-center gap-x-4 gap-y-1.5 px-5 py-3.5 text-left transition-colors hover:bg-surface-2',
                          selected?.id === t.id && 'bg-primary-soft hover:bg-primary-soft'
                        )}
                      >
                        <span className="w-24 shrink-0">
                          <span className="block text-[13px] font-medium text-fg">{capitalizar(fmt(inicio, 'EEE d MMM'))}</span>
                          <span className="block text-xs text-muted tabular">{formatHora(t.fecha_inicio)} – {formatHora(t.fecha_fin)}</span>
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block truncate font-medium text-fg">{t.cliente_nombre}</span>
                          <span className="block truncate text-[13px] text-muted">{t.servicio_nombre}</span>
                        </span>
                        <span className="flex shrink-0 gap-1.5 max-sm:w-full max-sm:pl-28">
                          {sinCerrar(t, ahora) && <Badge className="bg-warning-soft text-warning">Sin cerrar</Badge>}
                          <EstadoBadge estado={t.estado} />
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
              <Paginacion page={page} pages={pages} onChange={setPage} />
            </div>
          )}
        </Card>

        <div>
          {selected ? (
            <TurnoDetallePanel key={selected.id} turno={selected} onClose={() => setSelected(null)} onUpdated={onUpdated} />
          ) : (
            <div className="rounded-xl border border-dashed border-line-strong px-6 py-10 text-center text-[13px] text-muted max-lg:hidden">
              Elegí un turno para ver el detalle.
            </div>
          )}
        </div>
      </div>
    </>
  );
}
