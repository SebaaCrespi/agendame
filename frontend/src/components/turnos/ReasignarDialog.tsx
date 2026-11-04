import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { format } from 'date-fns';
import { AlertCircle } from 'lucide-react';
import { api } from '@/services/api';
import { Dialog } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
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
    <Dialog open={open} title="Reasignar turno" onClose={cerrar}>
      <form onSubmit={onSubmit} className="space-y-4">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {turno.cliente_nombre} · {turno.servicio_nombre}
        </p>
        <Input
          id="reasignar-fecha"
          label="Nueva fecha"
          type="date"
          min={hoy}
          value={fecha}
          onChange={(e) => {
            setFecha(e.target.value);
            setHora(null);
          }}
          required
        />

        <div>
          <p className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Horario</p>
          {loadingSlots ? (
            <p className="text-sm text-gray-500">Cargando horarios…</p>
          ) : slots.length === 0 ? (
            <p className="text-sm text-gray-500">No hay horarios libres ese día</p>
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
                      'rounded-md border px-2 py-1.5 text-sm transition-colors',
                      hora === s.hora_inicio
                        ? 'border-indigo-600 bg-indigo-600 text-white'
                        : 'border-gray-300 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800',
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

        {error && (
          <div role="alert" className="flex items-center gap-2 rounded bg-red-50 p-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
            <AlertCircle className="h-4 w-4 shrink-0" /> {error}
          </div>
        )}

        <div className="flex flex-wrap justify-end gap-2">
          <Button type="button" variant="outline" onClick={cerrar} disabled={saving}>
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
