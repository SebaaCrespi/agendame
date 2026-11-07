import { format } from 'date-fns';
import { es } from 'date-fns/locale';

/** Precio en centavos a pesos argentinos. */
export const formatPrecio = (centavos: number) =>
  new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(centavos / 100);

/** Fecha con locale español. */
export const fmt = (d: Date, patron: string) => format(d, patron, { locale: es });

/** "HH:MM" de un "HH:MM:SS". */
export const hhmm = (t: string | null | undefined) => (t ? t.slice(0, 5) : '');

/** Primera letra en mayúscula ("martes" → "Martes"). */
export const capitalizar = (s: string) => (s ? s[0].toUpperCase() + s.slice(1) : s);

/** "1 turno" / "3 turnos". */
export const plural = (n: number, singular: string, pluralForm = `${singular}s`) => `${n} ${n === 1 ? singular : pluralForm}`;
