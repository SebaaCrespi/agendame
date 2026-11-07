/**
 * Destino al que volver después de iniciar sesión o registrarse (`?next=`).
 * Solo rutas internas: evita redirecciones abiertas a otros sitios.
 */
export function destinoSeguro(next: string | null | undefined): string | null {
  if (!next || !next.startsWith('/') || next.startsWith('//') || next.startsWith('/\\')) return null;
  return next;
}

/** Ruta de la reserva logueada con lo elegido, lista para confirmar. */
export function destinoReserva(params: URLSearchParams): string {
  const p = new URLSearchParams(params);
  p.set('paso', 'confirmar');
  p.set('retomar', '1');
  return `/cliente/reservar?${p.toString()}`;
}
