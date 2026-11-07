interface ErrorDeCampo {
  field?: string;
  message?: string;
}

interface ProblemaApi {
  detail?: string;
  extra?: { errors?: ErrorDeCampo[] };
}

const datosProblema = (err: unknown) => (err as { response?: { data?: ProblemaApi } }).response?.data;

/** "body -> password" → "password". */
const nombreCampo = (field?: string) => field?.split(' -> ').pop();

/** Pydantic antepone "Value error, " a los mensajes de los validadores. */
const limpiarMensaje = (m: string) => m.replace(/^Value error,\s*/i, '');

/**
 * Mensaje para mostrar de un error del backend. En los 422 de validación usa
 * los mensajes de cada campo (ej. "La contraseña es demasiado común"); si no
 * hay, el `detail`; si tampoco, el texto por defecto.
 */
export function errorDetail(err: unknown, fallback: string): string {
  const data = datosProblema(err);
  if (!data?.detail) return fallback;
  const mensajes = (data.extra?.errors ?? [])
    .filter((e) => nombreCampo(e.field) !== 'body' && e.message)
    .map((e) => limpiarMensaje(e.message!));
  if (mensajes.length) return [...new Set(mensajes)].join('. ');
  const campos = (data.extra?.errors ?? [])
    .map((e) => nombreCampo(e.field))
    .filter((c): c is string => Boolean(c) && c !== 'body');
  return campos.length ? `${data.detail} (${[...new Set(campos)].join(', ')})` : data.detail;
}

/** Errores de validación por campo ({ password: "La contraseña es demasiado común" }). */
export function erroresPorCampo(err: unknown): Record<string, string> {
  const out: Record<string, string> = {};
  for (const e of datosProblema(err)?.extra?.errors ?? []) {
    const campo = nombreCampo(e.field);
    if (campo && campo !== 'body' && e.message && !out[campo]) out[campo] = limpiarMensaje(e.message);
  }
  return out;
}

/** Código HTTP de un error de axios, si lo hay. */
export function errorStatus(err: unknown): number | undefined {
  return (err as { response?: { status?: number } }).response?.status;
}
