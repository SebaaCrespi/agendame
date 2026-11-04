/** Mensaje `detail` del backend, o el texto por defecto si no hay. */
export function errorDetail(err: unknown, fallback: string): string {
  const e = err as { response?: { data?: { detail?: string } } };
  return e.response?.data?.detail || fallback;
}

/** Código HTTP de un error de axios, si lo hay. */
export function errorStatus(err: unknown): number | undefined {
  return (err as { response?: { status?: number } }).response?.status;
}
