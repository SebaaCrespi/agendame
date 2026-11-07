import { DateField } from '@/components/ui/DateField';
import { useCallback, useEffect, useState } from 'react';
import { CalendarDays } from 'lucide-react';
import { api } from '@/services/api';
import { Card } from '@/components/ui/Card';
import { Select } from '@/components/ui/Input';
import { Paginacion } from '@/components/ui/Paginacion';
import { Alerta } from '@/components/ui/Alerta';
import { EmptyState, PageHeader, Spinner } from '@/components/ui/misc';
import { ESTADO_LABEL, ESTADOS } from '@/components/turnos/estado';
import { errorDetail } from '@/components/turnos/errorDetail';
import { cn } from '@/utils/cn';
import { plural } from '@/utils/formato';
import { TablaTurnos } from './ResumenPage';
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
    <>
      <PageHeader title="Turnos" description="Todos los turnos del centro. Solo lectura: cada profesional gestiona los suyos." />

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Select aria-label="Profesional" value={profesionalId} onChange={(e) => filtrar(setProfesionalId)(e.target.value ? Number(e.target.value) : '')}>
          <option value="">Todos los profesionales</option>
          {profesionales.map((p) => (
            <option key={p.id} value={p.id}>{p.nombre} {p.apellido}</option>
          ))}
        </Select>
        <Select aria-label="Estado" value={estado} onChange={(e) => filtrar(setEstado)(e.target.value as TurnoEstado | '')}>
          <option value="">Todos los estados</option>
          {ESTADOS.map((e) => (
            <option key={e} value={e}>{ESTADO_LABEL[e]}</option>
          ))}
        </Select>
        <DateField aria-label="Desde" title="Desde" value={desde} max={hasta || undefined} onChange={filtrar(setDesde)} />
        <DateField aria-label="Hasta" title="Hasta" value={hasta} min={desde || undefined} onChange={filtrar(setHasta)} />
      </div>

      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}

      <Card padding="none" className="overflow-hidden">
        {loading && turnos.length === 0 ? (
          <Spinner />
        ) : turnos.length === 0 ? (
          <EmptyState icon={CalendarDays} title="Sin turnos" description="No hay turnos con estos filtros." />
        ) : (
          <div className={cn('transition-opacity', loading && 'opacity-50')}>
            <p className="border-b border-line px-5 py-3 text-[13px] text-muted">{plural(total, 'turno')}</p>
            <TablaTurnos turnos={turnos} conFecha />
            <Paginacion page={page} pages={pages} onChange={setPage} />
          </div>
        )}
      </Card>
    </>
  );
}
