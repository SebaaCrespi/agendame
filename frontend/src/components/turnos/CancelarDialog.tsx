import { useState, type FormEvent } from 'react';
import { AlertCircle } from 'lucide-react';
import { Dialog } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Input';
import { errorDetail } from './errorDetail';
import type { Turno } from '@/types';

interface CancelarDialogProps {
  open: boolean;
  /** Texto que identifica el turno (ej. "lunes 10 nov, 10:00 – Corte"). */
  resumen: string;
  /** Llamada al backend: cancelarTurnoCliente o cancelarTurnoProfesional. */
  cancelar: (motivo: string) => Promise<Turno>;
  onClose: () => void;
  onCancelado: (turno: Turno) => void;
}

const MAX_MOTIVO = 500;

export function CancelarDialog({ open, resumen, cancelar, onClose, onCancelado }: CancelarDialogProps) {
  const [motivo, setMotivo] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cerrar = () => {
    if (saving) return;
    setMotivo('');
    setError(null);
    onClose();
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const texto = motivo.trim();
    if (!texto) {
      setError('Indicá el motivo de la cancelación');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const turno = await cancelar(texto);
      setMotivo('');
      onCancelado(turno);
    } catch (err) {
      setError(errorDetail(err, 'No se pudo cancelar el turno'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} title="Cancelar turno" onClose={cerrar}>
      <form onSubmit={onSubmit} className="space-y-4">
        <p className="text-sm text-gray-600 dark:text-gray-400">{resumen}</p>
        <Textarea
          id="motivo-cancelacion"
          label="Motivo"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          maxLength={MAX_MOTIVO}
          rows={3}
          required
          helperText={`${motivo.length}/${MAX_MOTIVO}`}
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
          <Button type="submit" variant="destructive" loading={saving}>
            Cancelar turno
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
