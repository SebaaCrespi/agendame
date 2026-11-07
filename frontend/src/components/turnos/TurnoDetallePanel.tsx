import { useState } from 'react';
import { CalendarClock, Phone, RotateCcw, Stethoscope, UserRound, X, XCircle } from 'lucide-react';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Input';
import { Alerta } from '@/components/ui/Alerta';
import { capitalizar, fmt } from '@/utils/formato';
import { formatHora, parseHoraNegocio } from '@/utils/horaNegocio';
import { ACCION_LABEL, TRANSICIONES } from './estado';
import { EstadoBadge } from './EstadoBadge';
import { CancelarDialog } from './CancelarDialog';
import { ReasignarDialog } from './ReasignarDialog';
import { errorDetail } from './errorDetail';
import type { Turno, TurnoEstado } from '@/types';

/** Acciones de estado posibles ahora (ausente desde CONFIRMADO solo después de la hora de inicio, igual que el backend). */
export function accionesDisponibles(turno: Turno, ahora = new Date()): TurnoEstado[] {
  const yaEmpezo = parseHoraNegocio(turno.fecha_inicio) <= ahora;
  return TRANSICIONES[turno.estado].filter((d) => !(turno.estado === 'CONFIRMADO' && d === 'NO_ASISTIO' && !yaEmpezo));
}

interface TurnoDetallePanelProps {
  turno: Turno;
  onClose: () => void;
  onUpdated: (turno: Turno) => void;
}

export function TurnoDetallePanel({ turno, onClose, onUpdated }: TurnoDetallePanelProps) {
  const [notas, setNotas] = useState(turno.notas_profesional ?? '');
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dialogo, setDialogo] = useState<'cancelar' | 'reasignar' | null>(null);

  const inicio = parseHoraNegocio(turno.fecha_inicio);
  const yaEmpezo = inicio <= new Date();
  const acciones = accionesDisponibles(turno);

  // CU-08: pendientes/confirmados solo si todavía no empezaron; en curso se puede cancelar
  const futuro = (turno.estado === 'PENDIENTE' || turno.estado === 'CONFIRMADO') && !yaEmpezo;
  const puedeReasignar = futuro;
  const puedeCancelar = futuro || turno.estado === 'EN_CURSO';
  const resumen = `${fmt(inicio, "EEEE d MMM, HH:mm")} · ${turno.cliente_nombre} · ${turno.servicio_nombre}`;

  const cambiarEstado = async (destino: TurnoEstado) => {
    setSaving(destino);
    setError(null);
    try {
      onUpdated(await api.cambiarEstadoTurno(turno.id, destino));
    } catch (err) {
      setError(errorDetail(err, 'No se pudo cambiar el estado'));
    } finally {
      setSaving(null);
    }
  };

  const guardarNotas = async () => {
    setSaving('notas');
    setError(null);
    try {
      onUpdated(await api.agregarNotasTurno(turno.id, notas));
    } catch (err) {
      setError(errorDetail(err, 'No se pudieron guardar las notas'));
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="rounded-xl border border-line bg-surface lg:sticky lg:top-8">
      <div className="flex items-start justify-between gap-2 border-b border-line px-5 py-4">
        <div>
          <p className="text-[13px] text-muted">{capitalizar(fmt(inicio, "EEEE d 'de' MMMM"))}</p>
          <p className="text-lg font-semibold text-fg tabular">
            {formatHora(turno.fecha_inicio)} – {formatHora(turno.fecha_fin)}
          </p>
        </div>
        <button type="button" onClick={onClose} aria-label="Cerrar detalle" className="-mr-1.5 rounded-md p-1.5 text-subtle hover:bg-surface-2 hover:text-fg">
          <X className="size-4" />
        </button>
      </div>

      <div className="space-y-5 p-5">
        <EstadoBadge estado={turno.estado} />

        <dl className="space-y-2.5 text-sm">
          <Fila icon={UserRound} valor={turno.cliente_nombre} />
          {turno.cliente_telefono && (
            <Fila
              icon={Phone}
              valor={
                <a href={`tel:${turno.cliente_telefono}`} className="text-primary hover:underline">
                  {turno.cliente_telefono}
                </a>
              }
            />
          )}
          <Fila icon={Stethoscope} valor={turno.servicio_nombre} />
        </dl>

        {(turno.notas_cliente || turno.motivo_cancelacion || turno.reasignado_desde) && (
          <div className="space-y-1.5 rounded-lg bg-surface-2 px-3.5 py-3 text-[13px] text-muted">
            {turno.notas_cliente && <p><span className="font-medium text-fg">Nota del cliente:</span> {turno.notas_cliente}</p>}
            {turno.motivo_cancelacion && <p><span className="font-medium text-fg">Motivo de cancelación:</span> {turno.motivo_cancelacion}</p>}
            {turno.reasignado_desde && (
              <p className="flex items-start gap-1.5">
                <RotateCcw className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
                <span>
                  Reasignado desde el {fmt(parseHoraNegocio(turno.reasignado_desde), "d MMM, HH:mm")}
                  {turno.motivo_reasignacion && ` · ${turno.motivo_reasignacion}`}
                </span>
              </p>
            )}
          </div>
        )}

        {acciones.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {acciones.map((destino) => (
              <Button
                key={destino}
                size="sm"
                variant={destino === 'NO_ASISTIO' ? 'outline' : 'primary'}
                loading={saving === destino}
                disabled={saving !== null}
                onClick={() => cambiarEstado(destino)}
              >
                {ACCION_LABEL[destino]}
              </Button>
            ))}
          </div>
        )}

        {(puedeReasignar || puedeCancelar) && (
          <div className="flex flex-wrap gap-2">
            {puedeReasignar && (
              <Button size="sm" variant="outline" disabled={saving !== null} onClick={() => setDialogo('reasignar')}>
                <CalendarClock /> Reasignar
              </Button>
            )}
            {puedeCancelar && (
              <Button size="sm" variant="ghost" className="text-danger hover:text-danger" disabled={saving !== null} onClick={() => setDialogo('cancelar')}>
                <XCircle /> Cancelar turno
              </Button>
            )}
          </div>
        )}

        <div className="space-y-2 border-t border-line pt-5">
          <Textarea
            id={`notas-${turno.id}`}
            label="Notas internas"
            value={notas}
            onChange={(e) => setNotas(e.target.value)}
            maxLength={1000}
            rows={3}
            placeholder="Solo las ves vos"
          />
          <Button
            size="sm"
            variant="secondary"
            loading={saving === 'notas'}
            disabled={saving !== null || notas === (turno.notas_profesional ?? '')}
            onClick={guardarNotas}
          >
            Guardar notas
          </Button>
        </div>

        {error && <Alerta tipo="error">{error}</Alerta>}
      </div>

      <CancelarDialog
        open={dialogo === 'cancelar'}
        resumen={resumen}
        cancelar={(motivo) => api.cancelarTurnoProfesional(turno.id, motivo)}
        onClose={() => setDialogo(null)}
        onCancelado={(t) => {
          setDialogo(null);
          onUpdated(t);
        }}
      />
      {dialogo === 'reasignar' && (
        <ReasignarDialog
          open
          turno={turno}
          onClose={() => setDialogo(null)}
          onReasignado={(t) => {
            setDialogo(null);
            onUpdated(t);
          }}
        />
      )}
    </div>
  );
}

function Fila({ icon: Icon, valor }: { icon: typeof Phone; valor: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2.5">
      <Icon className="size-4 shrink-0 text-subtle" aria-hidden="true" />
      <dd className="min-w-0 truncate text-fg">{valor}</dd>
    </div>
  );
}
