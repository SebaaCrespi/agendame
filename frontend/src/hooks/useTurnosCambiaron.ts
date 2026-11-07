import { useEffect, useRef } from 'react';
import { EVENTO_TURNOS_CAMBIARON } from '@/components/turnos/estado';

/** Ejecuta `cb` cuando el asistente reserva o cancela un turno. */
export function useTurnosCambiaron(cb: () => void) {
  const ref = useRef(cb);
  useEffect(() => {
    ref.current = cb;
  }, [cb]);
  useEffect(() => {
    const h = () => ref.current();
    window.addEventListener(EVENTO_TURNOS_CAMBIARON, h);
    return () => window.removeEventListener(EVENTO_TURNOS_CAMBIARON, h);
  }, []);
}
