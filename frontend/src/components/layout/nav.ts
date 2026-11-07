import { CalendarDays, CalendarPlus, Clock, History, House, LayoutDashboard, Settings, Users } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { User } from '@/types';

export interface NavItem {
  path: string;
  label: string;
  /** Etiqueta corta para la barra inferior en mobile. */
  short?: string;
  icon: LucideIcon;
  /** Activo también en subrutas (ej. /profesional/configuracion/*). */
  prefix?: boolean;
}

export const NAV: Record<User['rol'], NavItem[]> = {
  CLIENTE: [
    { path: '/cliente/inicio', label: 'Inicio', icon: House },
    { path: '/cliente/reservar', label: 'Reservar', icon: CalendarPlus },
    { path: '/cliente/mis-turnos', label: 'Mis turnos', short: 'Turnos', icon: CalendarDays },
  ],
  PROVEEDOR: [
    { path: '/profesional/hoy', label: 'Hoy', icon: Clock },
    { path: '/profesional/agenda', label: 'Agenda', icon: CalendarDays },
    { path: '/profesional/historial', label: 'Historial', icon: History },
    { path: '/profesional/configuracion', label: 'Configuración', short: 'Ajustes', icon: Settings, prefix: true },
  ],
  ADMIN: [
    { path: '/admin/resumen', label: 'Resumen', icon: LayoutDashboard },
    { path: '/admin/turnos', label: 'Turnos', icon: CalendarDays },
    { path: '/admin/profesionales', label: 'Profesionales', icon: Users },
  ],
};

export const HOME_POR_ROL: Record<User['rol'], string> = {
  CLIENTE: '/cliente/inicio',
  PROVEEDOR: '/profesional/hoy',
  ADMIN: '/admin/resumen',
};

export const ROL_LABEL: Record<User['rol'], string> = {
  CLIENTE: 'Cliente',
  PROVEEDOR: 'Profesional',
  ADMIN: 'Administrador',
};
