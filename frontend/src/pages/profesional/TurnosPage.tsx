import { useCallback, useEffect, useState } from 'react';
import { addDays, format, startOfWeek } from 'date-fns';
import { es } from 'date-fns/locale';
import { AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { WeekGrid } from '@/components/turnos/WeekGrid';
import { TurnoDetallePanel } from '@/components/turnos/TurnoDetallePanel';
import { ESTADO_COLOR, ESTADO_LABEL, ESTADOS } from '@/components/turnos/estado';
import { cn } from '@/utils/cn';
import { minutosDeHora } from '@/utils/horaNegocio';
import type { Servicio, Turno, TurnoEstado } from '@/types';

const LIMITE = 100;
const RANGO_DEFAULT = { desde: 8 * 60, hasta: 20 * 60 };

export function ProfesionalTurnosPage() {
  const [inicioSemana, setInicioSemana] = useState(() => startOfWeek(new Date(), { weekStartsOn: 1 }));
  const [estado, setEstado] = useState<TurnoEstado | ''>('');
  const [servicioId, setServicioId] = useState<number | ''>('');
  const [cliente, setCliente] = useState('');
  const [clienteBuscado, setClienteBuscado] = useState('');

  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [total, setTotal] = useState(0);
  const [servicios, setServicios] = useState<Servicio[]>([]);
  const [rango, setRango] = useState(RANGO_DEFAULT);
  const [selected, setSelected] = useState<Turno | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Servicios (para el filtro) y rango horario de la grilla del profesional
  useEffect(() => {
    api.getMisServicios().then(setServicios).catch(() => setServicios([]));
    api
      .getMiGrilla()
      .then(({ grilla }) => {
        const activos = grilla.filter((d) => d.activo);
        if (activos.length === 0) return;
        setRango({
          desde: Math.min(...activos.map((d) => minutosDeHora(d.hora_inicio))),
          hasta: Math.max(...activos.map((d) => minutosDeHora(d.hora_fin))),
        });
      })
      .catch(() => setRango(RANGO_DEFAULT));
  }, []);

  // Debounce de la búsqueda por cliente
  useEffect(() => {
    const t = setTimeout(() => setClienteBuscado(cliente.trim()), 300);
    return () => clearTimeout(t);
  }, [cliente]);

  const cargar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getMisTurnosProfesional({
        desde: format(inicioSemana, 'yyyy-MM-dd'),
        hasta: format(addDays(inicioSemana, 6), 'yyyy-MM-dd'),
        page: 1,
        size: LIMITE,
        ...(estado && { estado }),
        ...(servicioId && { servicio_id: servicioId }),
        ...(clienteBuscado && { cliente: clienteBuscado }),
      });
      setTurnos(data.items);
      setTotal(data.total);
    } catch {
      setError('No se pudieron cargar los turnos');
    } finally {
      setLoading(false);
    }
  }, [inicioSemana, estado, servicioId, clienteBuscado]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  const onUpdated = (actualizado: Turno) => {
    const anterior = turnos.find((t) => t.id === actualizado.id);
    setTurnos((prev) => prev.map((t) => (t.id === actualizado.id ? actualizado : t)));
    setSelected(actualizado);
    // Reasignado (CU-08): puede haber salido de la semana o de los filtros
    if (anterior && anterior.fecha_inicio !== actualizado.fecha_inicio) cargar();
  };

  const finSemana = addDays(inicioSemana, 6);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Mis turnos</h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">
            Semana del {format(inicioSemana, 'd MMM', { locale: es })} al {format(finSemana, 'd MMM yyyy', { locale: es })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" aria-label="Semana anterior" onClick={() => setInicioSemana((d) => addDays(d, -7))}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={() => setInicioSemana(startOfWeek(new Date(), { weekStartsOn: 1 }))}>
            Hoy
          </Button>
          <Button variant="outline" size="sm" aria-label="Semana siguiente" onClick={() => setInicioSemana((d) => addDays(d, 7))}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Filtros */}
      <div className="grid gap-3 sm:grid-cols-3">
        <select
          aria-label="Filtrar por estado"
          value={estado}
          onChange={(e) => setEstado(e.target.value as TurnoEstado | '')}
          className="rounded-md border border-gray-300 bg-white p-2 text-sm text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
        >
          <option value="">Todos los estados</option>
          {ESTADOS.map((e) => (
            <option key={e} value={e}>{ESTADO_LABEL[e]}</option>
          ))}
        </select>
        <select
          aria-label="Filtrar por servicio"
          value={servicioId}
          onChange={(e) => setServicioId(e.target.value ? Number(e.target.value) : '')}
          className="rounded-md border border-gray-300 bg-white p-2 text-sm text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
        >
          <option value="">Todos los servicios</option>
          {servicios.map((s) => (
            <option key={s.id} value={s.id}>{s.nombre}</option>
          ))}
        </select>
        <input
          type="search"
          aria-label="Buscar cliente"
          placeholder="Buscar cliente…"
          value={cliente}
          onChange={(e) => setCliente(e.target.value)}
          className="rounded-md border border-gray-300 bg-white p-2 text-sm text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
        />
      </div>

      {/* Leyenda */}
      <div className="flex flex-wrap gap-2 text-xs">
        {ESTADOS.map((e) => (
          <span key={e} className={cn('rounded border px-2 py-0.5', ESTADO_COLOR[e])}>{ESTADO_LABEL[e]}</span>
        ))}
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
          <AlertCircle className="h-4 w-4" /> {error}
        </div>
      )}
      {total > LIMITE && (
        <p className="text-sm text-amber-600">Se muestran {LIMITE} de {total} turnos. Usá los filtros para acotar.</p>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className={cn('min-w-0 transition-opacity', loading && 'opacity-50')}>
          <WeekGrid
            inicioSemana={inicioSemana}
            turnos={turnos}
            desdeMin={rango.desde}
            hastaMin={rango.hasta}
            selectedId={selected?.id}
            onSelect={setSelected}
          />
          {!loading && turnos.length === 0 && (
            <p className="mt-3 text-center text-sm text-gray-500">No hay turnos esta semana con estos filtros.</p>
          )}
        </div>
        <div>
          {selected ? (
            <TurnoDetallePanel key={selected.id} turno={selected} onClose={() => setSelected(null)} onUpdated={onUpdated} />
          ) : (
            <p className="rounded-lg border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500 dark:border-gray-700">
              Elegí un turno de la grilla para ver el detalle.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
