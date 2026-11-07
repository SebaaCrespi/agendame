import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CalendarDays, CalendarPlus } from 'lucide-react';
import { api } from '@/services/api';
import { buttonClass } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input, Select } from '@/components/ui/Input';
import { Paginacion } from '@/components/ui/Paginacion';
import { Alerta } from '@/components/ui/Alerta';
import { EmptyState, PageHeader, Segmented, Spinner } from '@/components/ui/misc';
import { CancelarDialog } from '@/components/turnos/CancelarDialog';
import { TurnoClienteItem, puedeCancelar } from '@/components/turnos/TurnoClienteItem';
import { GRUPOS_ESTADO, estadosDelGrupo, type GrupoEstado } from '@/components/turnos/estado';
import { useTurnosCambiaron } from '@/hooks/useTurnosCambiaron';
import { cn } from '@/utils/cn';
import { fmt, plural } from '@/utils/formato';
import { parseHoraNegocio } from '@/utils/horaNegocio';
import type { MomentoTurno, Turno } from '@/types';

const POR_PAGINA = 10;

/** CU-09: turnos del cliente, próximos y pasados, con filtros y cancelación (CU-08). */
export function MisTurnosPage() {
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
  const [aCancelar, setACancelar] = useState<Turno | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

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
  useTurnosCambiaron(() => void cargar());

  // Cualquier cambio de filtro vuelve a la primera página
  const filtrar = <T,>(set: (v: T) => void) => (v: T) => {
    set(v);
    setPage(1);
  };

  const sinFiltros = grupo === 'todos' && !desde && !hasta;

  return (
    <>
      <PageHeader
        title="Mis turnos"
        description="Tus próximas citas y tu historial."
        actions={
          <Link to="/cliente/reservar" className={buttonClass('primary')}>
            <CalendarPlus /> Reservar turno
          </Link>
        }
      />

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <Segmented
          label="Momento"
          value={momento}
          onChange={filtrar(setMomento)}
          options={[
            { value: 'proximos', label: 'Próximos' },
            { value: 'pasados', label: 'Pasados' },
          ]}
        />
        <div className="ml-auto grid w-full grid-cols-1 gap-3 sm:w-auto sm:grid-cols-3">
          <Select aria-label="Filtrar por estado" value={grupo} onChange={(e) => filtrar(setGrupo)(e.target.value as GrupoEstado)} wrapperClassName="sm:w-44">
            {(Object.keys(GRUPOS_ESTADO) as GrupoEstado[]).map((g) => (
              <option key={g} value={g}>{g === 'todos' ? 'Todos los estados' : GRUPOS_ESTADO[g].label}</option>
            ))}
          </Select>
          <Input type="date" aria-label="Desde" title="Desde" value={desde} max={hasta || undefined} onChange={(e) => filtrar(setDesde)(e.target.value)} />
          <Input type="date" aria-label="Hasta" title="Hasta" value={hasta} min={desde || undefined} onChange={(e) => filtrar(setHasta)(e.target.value)} />
        </div>
      </div>

      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}
      {aviso && <Alerta tipo="ok" className="mb-4">{aviso}</Alerta>}

      <Card padding="none" className="overflow-hidden">
        {loading && turnos.length === 0 ? (
          <Spinner />
        ) : turnos.length === 0 ? (
          <EmptyState
            icon={CalendarDays}
            title={momento === 'proximos' ? 'No tenés turnos próximos' : 'No hay turnos pasados'}
            description={sinFiltros ? (momento === 'proximos' ? 'Cuando reserves, van a aparecer acá.' : undefined) : 'Probá con otros filtros.'}
            action={
              momento === 'proximos' && sinFiltros ? (
                <Link to="/cliente/reservar" className={buttonClass('primary')}>
                  Reservar un turno
                </Link>
              ) : undefined
            }
          />
        ) : (
          <div className={cn('transition-opacity', loading && 'opacity-50')}>
            <p className="border-b border-line px-5 py-3 text-[13px] text-muted">{plural(total, 'turno')}</p>
            <ul className="divide-y divide-line">
              {turnos.map((t) => (
                <TurnoClienteItem key={t.id} turno={t} onCancelar={puedeCancelar(t, ahora) ? () => setACancelar(t) : undefined} />
              ))}
            </ul>
            <Paginacion page={page} pages={pages} onChange={setPage} />
          </div>
        )}
      </Card>

      {aCancelar && (
        <CancelarDialog
          open
          resumen={`${fmt(parseHoraNegocio(aCancelar.fecha_inicio), "EEEE d MMM, HH:mm")} · ${aCancelar.servicio_nombre} con ${aCancelar.profesional_nombre}`}
          cancelar={(motivo) => api.cancelarTurnoCliente(aCancelar.id, motivo)}
          onClose={() => setACancelar(null)}
          onCancelado={() => {
            setACancelar(null);
            setAviso('Turno cancelado');
            void cargar();
          }}
        />
      )}
    </>
  );
}
