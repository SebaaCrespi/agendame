import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { LogOut, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { ChatWidget } from '@/components/chat/ChatWidget';
import { Avatar } from '@/components/ui/misc';
import { cn } from '@/utils/cn';
import { Brand } from './Brand';
import { ThemeToggle } from './ThemeToggle';
import { HOME_POR_ROL, NAV, ROL_LABEL, type NavItem } from './nav';

const CLAVE_COLAPSADO = 'agendame_sidebar_colapsado';

function leerColapsado(): boolean {
  try {
    return localStorage.getItem(CLAVE_COLAPSADO) === '1';
  } catch {
    return false;
  }
}

function useActivo() {
  const { pathname } = useLocation();
  return (item: NavItem) => (item.prefix ? pathname.startsWith(item.path) : pathname === item.path);
}

/** Layout autenticado: sidebar por rol en desktop, barra inferior en mobile. */
export function AppShell() {
  const { user, logout } = useAuth();
  const [colapsado, setColapsado] = useState(leerColapsado);
  const activo = useActivo();

  if (!user) return null;
  const items = NAV[user.rol];

  const toggle = () => {
    setColapsado((c) => {
      try {
        localStorage.setItem(CLAVE_COLAPSADO, c ? '0' : '1');
      } catch {
        // sin storage: no se recuerda
      }
      return !c;
    });
  };

  return (
    <div className="min-h-screen bg-canvas">
      <a href="#contenido" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[70] focus:rounded-lg focus:bg-surface focus:px-4 focus:py-2 focus:shadow-pop">
        Saltar al contenido
      </a>

      {/* Sidebar desktop */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-line bg-surface transition-[width] duration-200 md:flex',
          colapsado ? 'w-[68px]' : 'w-60'
        )}
      >
        <div className={cn('flex h-16 items-center', colapsado ? 'justify-center px-2' : 'justify-between px-4')}>
          <Brand to={HOME_POR_ROL[user.rol]} compact={colapsado} />
          {!colapsado && (
            <button type="button" onClick={toggle} aria-label="Contraer menú" className="rounded-md p-1.5 text-subtle hover:bg-surface-2 hover:text-fg">
              <PanelLeftClose className="size-4" />
            </button>
          )}
        </div>

        <nav aria-label="Navegación principal" className="flex-1 space-y-0.5 px-3 py-2">
          {items.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              title={colapsado ? item.label : undefined}
              className={cn(
                'flex h-9 items-center gap-3 rounded-lg px-2.5 text-sm font-medium transition-colors',
                colapsado && 'justify-center px-0',
                activo(item) ? 'bg-primary-soft text-primary' : 'text-muted hover:bg-surface-2 hover:text-fg'
              )}
              aria-current={activo(item) ? 'page' : undefined}
            >
              <item.icon className="size-[18px] shrink-0" aria-hidden="true" />
              {!colapsado && item.label}
            </NavLink>
          ))}
        </nav>

        <div className="space-y-3 border-t border-line p-3">
          {colapsado ? (
            <button type="button" onClick={toggle} aria-label="Expandir menú" className="mx-auto flex rounded-md p-2 text-subtle hover:bg-surface-2 hover:text-fg">
              <PanelLeftOpen className="size-4" />
            </button>
          ) : (
            <ThemeToggle className="flex w-full" />
          )}
          <div className={cn('flex items-center gap-2.5', colapsado && 'flex-col')}>
            <Avatar nombre={user.nombre} size="sm" />
            {!colapsado && (
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-medium text-fg">{user.nombre}</p>
                <p className="truncate text-xs text-muted">{ROL_LABEL[user.rol]}</p>
              </div>
            )}
            <button
              type="button"
              onClick={logout}
              aria-label="Cerrar sesión"
              title="Cerrar sesión"
              className="rounded-md p-1.5 text-subtle transition-colors hover:bg-surface-2 hover:text-danger"
            >
              <LogOut className="size-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Cabecera mobile */}
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-line bg-surface/90 px-4 backdrop-blur md:hidden">
        <Brand to={HOME_POR_ROL[user.rol]} />
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <button type="button" onClick={logout} aria-label="Cerrar sesión" className="rounded-md p-2 text-subtle hover:bg-surface-2 hover:text-danger">
            <LogOut className="size-4" />
          </button>
        </div>
      </header>

      <main
        id="contenido"
        className={cn('pb-24 transition-[padding] duration-200 md:pb-12', colapsado ? 'md:pl-[68px]' : 'md:pl-60')}
      >
        <div className="mx-auto w-full max-w-6xl px-4 pt-6 sm:px-6 md:px-8 md:pt-8">
          <Outlet />
        </div>
      </main>

      {/* Barra inferior mobile */}
      <nav
        aria-label="Navegación principal"
        className="fixed inset-x-0 bottom-0 z-30 flex border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"
      >
        {items.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            aria-current={activo(item) ? 'page' : undefined}
            className={cn(
              'flex h-16 flex-1 flex-col items-center justify-center gap-1 text-[11px] font-medium',
              activo(item) ? 'text-primary' : 'text-muted'
            )}
          >
            <item.icon className="size-5" aria-hidden="true" />
            {item.short ?? item.label}
          </NavLink>
        ))}
      </nav>

      {user.rol === 'CLIENTE' && <ChatWidget />}
    </div>
  );
}
