import { useCallback, useEffect, useState } from 'react';
import { addDays, format, startOfWeek } from 'date-fns';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input, Select } from '@/components/ui/Input';
import { Alerta } from '@/components/ui/Alerta';
import { PageHeader } from '@/components/ui/misc';
import { WeekGrid } from '@/components/turnos/WeekGrid';
import { TurnoDetallePanel } from '@/components/turnos/TurnoDetallePanel';
import { ESTADO_LABEL, ESTADO_PUNTO, ESTADOS } from '@/components/turnos/estado';
import { cn } from '@/utils/cn';
import { fmt } from '@/utils/formato';
import { minutosDeHora } from '@/utils/horaNegocio';
import type { Servicio, Turno, TurnoEstado } from '@/types';

const LIMITE = 100;
const RANGO_DEFAULT = { desde: 8 * 60, hasta: 20 * 60 };
/** Estados que se muestran en la leyenda (los cancelados comparten color). */
const LEYENDA: TurnoEstado[] = ['PENDIENTE', 'CONFIRMADO', 'EN_CURSO', 'FINALIZADO', 'CANCELADO_CLIENTE'];

/** CU-07: grilla semanal del profesional. */
export function ProfesionalAgendaPage() {
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
        ...(estado && { estado: [estado] }),
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
    void cargar();
  }, [cargar]);

  const onUpdated = (actualizado: Turno) => {
    const anterior = turnos.find((t) => t.id === actualizado.id);
    setTurnos((prev) => prev.map((t) => (t.id === actualizado.id ? actualizado : t)));
    setSelected(actualizado);
    // Reasignado (CU-08): puede haber salido de la semana o de los filtros
    if (anterior && anterior.fecha_inicio !== actualizado.fecha_inicio) void cargar();
  };

  const finSemana = addDays(inicioSemana, 6);
  const mismoMes = inicioSemana.getMonth() === finSemana.getMonth();

  return (
    <>
      <PageHeader
        title="Agenda"
        description={`${fmt(inicioSemana, mismoMes ? 'd' : 'd MMM')} – ${fmt(finSemana, "d 'de' MMMM yyyy")}`}
        actions={
          <div className="flex items-center gap-1.5">
            <Button variant="outline" size="icon" aria-label="Semana anterior" onClick={() => setInicioSemana((d) => addDays(d, -7))}>
              <ChevronLeft />
            </Button>
            <Button variant="outline" onClick={() => setInicioSemana(startOfWeek(new Date(), { weekStartsOn: 1 }))}>
              Hoy
            </Button>
            <Button variant="outline" size="icon" aria-label="Semana siguiente" onClick={() => setInicioSemana((d) => addDays(d, 7))}>
              <ChevronRight />
            </Button>
          </div>
        }
      />

      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <Input type="search" aria-label="Buscar cliente" placeholder="Buscar cliente…" leftIcon={<Search />} value={cliente} onChange={(e) => setCliente(e.target.value)} />
        <Select aria-label="Filtrar por estado" value={estado} onChange={(e) => setEstado(e.target.value as TurnoEstado | '')}>
          <option value="">Todos los estados</option>
          {ESTADOS.map((e) => (
            <option key={e} value={e}>{ESTADO_LABEL[e]}</option>
          ))}
        </Select>
        <Select aria-label="Filtrar por servicio" value={servicioId} onChange={(e) => setServicioId(e.target.value ? Number(e.target.value) : '')}>
          <option value="">Todos los servicios</option>
          {servicios.map((s) => (
            <option key={s.id} value={s.id}>{s.nombre}</option>
          ))}
        </Select>
      </div>

      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}
      {total > LIMITE && (
        <Alerta tipo="aviso" className="mb-4">
          Se muestran {LIMITE} de {total} turnos. Usá los filtros para acotar.
        </Alerta>
      )}

      <div className="grid items-start gap-6 xl:grid-cols-[1fr_320px]">
        <Card padding="none" className={cn('min-w-0 overflow-hidden transition-opacity', loading && 'opacity-60')}>
          <WeekGrid inicioSemana={inicioSemana} turnos={turnos} desdeMin={rango.desde} hastaMin={rango.hasta} selectedId={selected?.id} onSelect={setSelected} />
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-line px-5 py-3 text-xs text-muted">
            {LEYENDA.map((e) => (
              <span key={e} className="flex items-center gap-1.5">
                <span className={cn('size-2 rounded-full', ESTADO_PUNTO[e])} aria-hidden="true" />
                {e === 'CANCELADO_CLIENTE' ? 'Cancelado' : ESTADO_LABEL[e]}
              </span>
            ))}
            {!loading && turnos.length === 0 && <span className="ml-auto">No hay turnos esta semana con estos filtros.</span>}
          </div>
        </Card>
        <div>
          {selected ? (
            <TurnoDetallePanel key={selected.id} turno={selected} onClose={() => setSelected(null)} onUpdated={onUpdated} />
          ) : (
            <div className="rounded-xl border border-dashed border-line-strong px-6 py-10 text-center text-[13px] text-muted">
              Elegí un turno de la grilla para ver el detalle.
            </div>
          )}
        </div>
      </div>
    </>
  );
}
