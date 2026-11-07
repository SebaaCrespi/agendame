import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { CalendarCheck, CalendarX, Plus, UserCheck, UserX } from 'lucide-react';
import { api } from '@/services/api';
import { buttonClass } from '@/components/ui/Button';
import { Card, CardSection } from '@/components/ui/Card';
import { Alerta } from '@/components/ui/Alerta';
import { EmptyState, PageHeader, Spinner, Stat } from '@/components/ui/misc';
import { EstadoBadge } from '@/components/turnos/EstadoBadge';
import { ES_CANCELADO, ESTADO_LABEL, ESTADO_PUNTO } from '@/components/turnos/estado';
import { cn } from '@/utils/cn';
import { capitalizar, fmt } from '@/utils/formato';
import { formatHora, parseHoraNegocio } from '@/utils/horaNegocio';
import type { Turno, TurnoEstado } from '@/types';

/** Orden de los estados en la barra de resumen. */
const ORDEN: TurnoEstado[] = ['FINALIZADO', 'EN_CURSO', 'CONFIRMADO', 'PENDIENTE', 'NO_ASISTIO', 'CANCELADO_CLIENTE', 'CANCELADO_PROFESIONAL'];

/** Resumen del día para el administrador. */
export function AdminResumenPage() {
  const [activos, setActivos] = useState<number | null>(null);
  const [inactivos, setInactivos] = useState<number | null>(null);
  const [turnos, setTurnos] = useState<Turno[] | null>(null);
  const [totalHoy, setTotalHoy] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [ahora] = useState(() => new Date());

  useEffect(() => {
    const hoy = format(new Date(), 'yyyy-MM-dd');
    api.getProfesionalesAdmin({ size: 1, activo: true }).then((d) => setActivos(d.total)).catch(() => setActivos(null));
    api.getProfesionalesAdmin({ size: 1, activo: false }).then((d) => setInactivos(d.total)).catch(() => setInactivos(null));
    api
      .getAllTurnosAdmin({ desde: hoy, hasta: hoy, page: 1, size: 100 })
      .then((d) => {
        setTurnos([...d.items].sort((a, b) => a.fecha_inicio.localeCompare(b.fecha_inicio)));
        setTotalHoy(d.total);
      })
      .catch(() => {
        setTurnos([]);
        setError('No se pudieron cargar los turnos de hoy');
      });
  }, []);

  const conteo = (turnos ?? []).reduce<Partial<Record<TurnoEstado, number>>>((acc, t) => {
    acc[t.estado] = (acc[t.estado] ?? 0) + 1;
    return acc;
  }, {});
  const cancelados = (conteo.CANCELADO_CLIENTE ?? 0) + (conteo.CANCELADO_PROFESIONAL ?? 0);
  const n = turnos?.length ?? 0;
  const proximos = (turnos ?? []).filter((t) => !ES_CANCELADO(t.estado) && parseHoraNegocio(t.fecha_fin) > ahora).slice(0, 8);

  return (
    <>
      <PageHeader
        title="Resumen"
        description={capitalizar(fmt(ahora, "EEEE d 'de' MMMM"))}
        actions={
          <Link to="/admin/profesionales?nuevo=1" className={buttonClass('primary')}>
            <Plus /> Nuevo profesional
          </Link>
        }
      />

      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}

      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Profesionales activos" value={activos ?? '—'} icon={UserCheck} />
        <Stat label="Inactivos" value={inactivos ?? '—'} icon={UserX} />
        <Stat label="Turnos hoy" value={turnos ? totalHoy : '—'} icon={CalendarCheck} />
        <Stat label="Cancelaciones hoy" value={turnos ? cancelados : '—'} icon={CalendarX} />
      </div>

      {n > 0 && (
        <Card className="mb-6">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-[15px] font-semibold text-fg">Turnos de hoy por estado</h2>
            <span className="text-[13px] text-muted">{n} total</span>
          </div>
          <div className="flex h-2.5 overflow-hidden rounded-full bg-surface-2" role="img" aria-label="Distribución de turnos por estado">
            {ORDEN.filter((e) => conteo[e]).map((e) => (
              <span key={e} className={ESTADO_PUNTO[e]} style={{ width: `${((conteo[e] ?? 0) / n) * 100}%` }} />
            ))}
          </div>
          <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-[13px] text-muted">
            {ORDEN.filter((e) => conteo[e]).map((e) => (
              <li key={e} className="flex items-center gap-1.5">
                <span className={cn('size-2 rounded-full', ESTADO_PUNTO[e])} aria-hidden="true" />
                {ESTADO_LABEL[e]} <span className="font-medium text-fg tabular">{conteo[e]}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card padding="none" className="overflow-hidden">
        <CardSection
          title="Próximos turnos de hoy"
          actions={
            <Link to="/admin/turnos" className="text-[13px] font-medium text-primary hover:underline">
              Ver todos
            </Link>
          }
        />
        {turnos === null ? (
          <Spinner />
        ) : proximos.length === 0 ? (
          <EmptyState icon={CalendarCheck} title="No quedan turnos para hoy" />
        ) : (
          <TablaTurnos turnos={proximos} />
        )}
      </Card>
    </>
  );
}

/** Tabla de turnos (también la usa la página de turnos). */
export function TablaTurnos({ turnos, conFecha = false }: { turnos: Turno[]; conFecha?: boolean }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="bg-surface-2 text-xs text-muted">
          <tr>
            {conFecha && <th className="px-5 py-2.5 font-medium">Fecha</th>}
            <th className="px-5 py-2.5 font-medium">Hora</th>
            <th className="px-5 py-2.5 font-medium">Cliente</th>
            <th className="px-5 py-2.5 font-medium">Profesional</th>
            <th className="px-5 py-2.5 font-medium">Servicio</th>
            <th className="px-5 py-2.5 font-medium">Estado</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {turnos.map((t) => (
            <tr key={t.id} className="transition-colors hover:bg-surface-2/60">
              {conFecha && <td className="whitespace-nowrap px-5 py-3 font-medium text-fg">{capitalizar(fmt(parseHoraNegocio(t.fecha_inicio), 'EEE d MMM'))}</td>}
              <td className="whitespace-nowrap px-5 py-3 text-fg tabular">{formatHora(t.fecha_inicio)} – {formatHora(t.fecha_fin)}</td>
              <td className="whitespace-nowrap px-5 py-3 text-fg">{t.cliente_nombre}</td>
              <td className="whitespace-nowrap px-5 py-3 text-muted">{t.profesional_nombre}</td>
              <td className="whitespace-nowrap px-5 py-3 text-muted">{t.servicio_nombre}</td>
              <td className="px-5 py-3"><EstadoBadge estado={t.estado} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
