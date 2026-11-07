import { useState, type FormEvent } from 'react';
import { Dialog } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Input';
import { Alerta } from '@/components/ui/Alerta';
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
    <Dialog open={open} title="Cancelar turno" description={resumen} onClose={cerrar}>
      <form onSubmit={onSubmit} className="space-y-4">
        <Textarea
          id="motivo-cancelacion"
          label="Motivo"
          placeholder="Contanos brevemente por qué"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          maxLength={MAX_MOTIVO}
          rows={3}
          required
          helperText={`${motivo.length}/${MAX_MOTIVO}`}
        />
        {error && <Alerta tipo="error">{error}</Alerta>}
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="outline" onClick={cerrar} disabled={saving}>
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
