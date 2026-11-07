import { DateField } from '@/components/ui/DateField';
import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { format } from 'date-fns';
import { api } from '@/services/api';
import { Dialog } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Input';
import { Alerta } from '@/components/ui/Alerta';
import { cn } from '@/utils/cn';
import { parseHoraNegocio } from '@/utils/horaNegocio';
import { errorDetail, errorStatus } from './errorDetail';
import type { SlotDisponible, Turno } from '@/types';

interface ReasignarDialogProps {
  open: boolean;
  turno: Turno;
  onClose: () => void;
  onReasignado: (turno: Turno) => void;
}

const MAX_MOTIVO = 500;

export function ReasignarDialog({ open, turno, onClose, onReasignado }: ReasignarDialogProps) {
  const [hoy] = useState(() => format(new Date(), 'yyyy-MM-dd'));
  const [fecha, setFecha] = useState(() => format(parseHoraNegocio(turno.fecha_inicio), 'yyyy-MM-dd'));
  const [slots, setSlots] = useState<SlotDisponible[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [hora, setHora] = useState<string | null>(null);
  const [motivo, setMotivo] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const horaActual = format(parseHoraNegocio(turno.fecha_inicio), 'HH:mm');
  const fechaActual = format(parseHoraNegocio(turno.fecha_inicio), 'yyyy-MM-dd');

  const cargarSlots = useCallback(async (dia: string) => {
    setLoadingSlots(true);
    try {
      const data = await api.getMisSlots({
        desde: dia,
        hasta: dia,
        servicio_id: turno.servicio_id,
        excluir_turno_id: turno.id,
      });
      setSlots(data.slots.filter((s) => s.disponible));
    } catch (err) {
      setSlots([]);
      setError(errorDetail(err, 'No se pudieron cargar los horarios'));
    } finally {
      setLoadingSlots(false);
    }
  }, [turno.id, turno.servicio_id]);

  useEffect(() => {
    if (open && fecha) void cargarSlots(fecha);
  }, [open, fecha, cargarSlots]);

  const cerrar = () => {
    if (saving) return;
    setError(null);
    setMotivo('');
    setHora(null);
    onClose();
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!hora) {
      setError('Elegí un horario');
      return;
    }
    const texto = motivo.trim();
    if (!texto) {
      setError('Indicá el motivo de la reasignación');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const actualizado = await api.reasignarTurno(turno.id, {
        nueva_fecha: fecha,
        nueva_hora_inicio: hora,
        motivo: texto,
      });
      setMotivo('');
      onReasignado(actualizado);
    } catch (err) {
      setError(errorDetail(err, 'No se pudo reasignar el turno'));
      // El horario pudo haberse ocupado: refrescar los slots
      if (errorStatus(err) === 409) {
        setHora(null);
        cargarSlots(fecha);
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} title="Reasignar turno" description={`${turno.cliente_nombre} · ${turno.servicio_nombre}`} onClose={cerrar}>
      <form onSubmit={onSubmit} className="space-y-4">
        <DateField
          id="reasignar-fecha"
          label="Nueva fecha"
          min={hoy}
          value={fecha}
          onChange={(v) => {
            setFecha(v);
            setHora(null);
          }}
          required
        />

        <div>
          <p className="mb-1.5 text-[13px] font-medium text-fg">Horario</p>
          {loadingSlots ? (
            <p className="text-[13px] text-muted">Cargando horarios…</p>
          ) : slots.length === 0 ? (
            <p className="rounded-lg bg-surface-2 px-3 py-2.5 text-[13px] text-muted">No hay horarios libres ese día</p>
          ) : (
            <div className="grid grid-cols-4 gap-2 sm:grid-cols-5" role="radiogroup" aria-label="Horarios libres">
              {slots.map((s) => {
                const hhmm = s.hora_inicio.slice(0, 5);
                const esActual = fecha === fechaActual && hhmm === horaActual;
                return (
                  <button
                    key={s.hora_inicio}
                    type="button"
                    role="radio"
                    aria-checked={hora === s.hora_inicio}
                    disabled={esActual}
                    title={esActual ? 'Horario actual del turno' : undefined}
                    onClick={() => setHora(s.hora_inicio)}
                    className={cn(
                      'h-9 rounded-lg border text-sm font-medium tabular transition-colors',
                      hora === s.hora_inicio
                        ? 'border-primary bg-primary text-on-primary'
                        : 'border-line bg-surface text-fg hover:border-primary hover:text-primary',
                      esActual && 'cursor-not-allowed opacity-40'
                    )}
                  >
                    {hhmm}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <Textarea
          id="motivo-reasignacion"
          label="Motivo"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          maxLength={MAX_MOTIVO}
          rows={2}
          required
        />

        {error && <Alerta tipo="error">{error}</Alerta>}

        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="outline" onClick={cerrar} disabled={saving}>
            Volver
          </Button>
          <Button type="submit" loading={saving} disabled={!hora}>
            Reasignar
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
