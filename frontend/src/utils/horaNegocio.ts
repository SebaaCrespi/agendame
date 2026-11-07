import { format } from 'date-fns';

/**
 * Los horarios de turnos son "hora de reloj del negocio". La API a veces los
 * devuelve con sufijo de zona (+00:00 / Z) y a veces sin él. Descartamos la
 * zona y los parseamos como hora local, para que 10:00 se vea como 10:00 sin
 * importar la zona horaria del navegador.
 */
export function parseHoraNegocio(iso: string): Date {
  const sinZona = iso.replace(/(Z|[+-]\d{2}:?\d{2})$/, '');
  return new Date(sinZona.includes('T') ? sinZona : `${sinZona}T00:00:00`);
}

/** HH:mm de un datetime ISO de turno. */
export function formatHora(iso: string): string {
  return format(parseHoraNegocio(iso), 'HH:mm');
}

/** Minutos desde la medianoche de un datetime ISO de turno. */
export function minutosDelDia(iso: string): number {
  const d = parseHoraNegocio(iso);
  return d.getHours() * 60 + d.getMinutes();
}

/** Minutos desde la medianoche de un "HH:MM[:SS]". */
export function minutosDeHora(hhmm: string): number {
  const [h, m] = hhmm.split(':').map(Number);
  return h * 60 + (m || 0);
}
