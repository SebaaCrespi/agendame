interface ProblemaApi {
  detail?: string;
  extra?: { errors?: { field?: string }[] };
}

/**
 * Mensaje `detail` del backend, o el texto por defecto si no hay. En los 422 de
 * validación agrega los campos con error, ej. "Error de validación… (email)".
 */
export function errorDetail(err: unknown, fallback: string): string {
  const data = (err as { response?: { data?: ProblemaApi } }).response?.data;
  if (!data?.detail) return fallback;
  const campos = (data.extra?.errors ?? [])
    .map((e) => e.field?.split(' -> ').pop())
    .filter((c): c is string => Boolean(c) && c !== 'body');
  return campos.length ? `${data.detail} (${[...new Set(campos)].join(', ')})` : data.detail;
}

/** Código HTTP de un error de axios, si lo hay. */
export function errorStatus(err: unknown): number | undefined {
  return (err as { response?: { status?: number } }).response?.status;
}
