import { useState } from 'react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { AlertCircle, Clock, Phone, Scissors, User, X } from 'lucide-react';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';
import { formatHora, parseHoraNegocio } from '@/utils/horaNegocio';
import { ACCION_LABEL, ESTADO_COLOR, ESTADO_LABEL, TRANSICIONES } from './estado';
import type { Turno, TurnoEstado } from '@/types';

interface TurnoDetallePanelProps {
  turno: Turno;
  onClose: () => void;
  onUpdated: (turno: Turno) => void;
}

function errorDetail(err: unknown, fallback: string): string {
  const e = err as { response?: { data?: { detail?: string } } };
  return e.response?.data?.detail || fallback;
}

export function TurnoDetallePanel({ turno, onClose, onUpdated }: TurnoDetallePanelProps) {
  const [notas, setNotas] = useState(turno.notas_profesional ?? '');
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const yaEmpezo = parseHoraNegocio(turno.fecha_inicio) <= new Date();
  const acciones = TRANSICIONES[turno.estado].filter(
    // Ausente desde CONFIRMADO solo después de la hora de inicio (igual que el backend)
    (destino) => !(turno.estado === 'CONFIRMADO' && destino === 'NO_ASISTIO' && !yaEmpezo)
  );

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
    <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-4 text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm capitalize text-gray-500 dark:text-gray-400">
            {format(parseHoraNegocio(turno.fecha_inicio), 'EEEE d MMMM', { locale: es })}
          </p>
          <p className="flex items-center gap-1 text-lg font-semibold">
            <Clock className="h-4 w-4" /> {formatHora(turno.fecha_inicio)} – {formatHora(turno.fecha_fin)}
          </p>
        </div>
        <button type="button" onClick={onClose} aria-label="Cerrar detalle" className="text-gray-400 hover:text-gray-600">
          <X className="h-5 w-5" />
        </button>
      </div>

      <span className={cn('inline-block rounded border px-2 py-0.5 text-xs font-medium', ESTADO_COLOR[turno.estado])}>
        {ESTADO_LABEL[turno.estado]}
      </span>

      <div className="space-y-1 text-sm">
        <p className="flex items-center gap-2"><User className="h-4 w-4 text-gray-400" /> {turno.cliente_nombre}</p>
        {turno.cliente_telefono && (
          <p className="flex items-center gap-2"><Phone className="h-4 w-4 text-gray-400" /> {turno.cliente_telefono}</p>
        )}
        <p className="flex items-center gap-2"><Scissors className="h-4 w-4 text-gray-400" /> {turno.servicio_nombre}</p>
        {turno.notas_cliente && (
          <p className="text-gray-500 dark:text-gray-400">Nota del cliente: {turno.notas_cliente}</p>
        )}
      </div>

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

      <div className="space-y-2">
        <label htmlFor="notas-profesional" className="text-sm font-medium">Notas internas</label>
        <textarea
          id="notas-profesional"
          value={notas}
          onChange={(e) => setNotas(e.target.value)}
          maxLength={1000}
          rows={3}
          className="w-full rounded-md border border-gray-300 bg-white p-2 text-sm dark:border-gray-600 dark:bg-gray-800"
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

      {error && (
        <div className="flex items-center gap-2 rounded bg-red-50 p-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
          <AlertCircle className="h-4 w-4" /> {error}
        </div>
      )}
    </div>
  );
}
