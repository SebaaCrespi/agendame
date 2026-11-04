import { Link, NavLink } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';
import { Menu, X, LogOut, User, LayoutDashboard, Calendar, Settings, Building2, History as HistoryIcon } from 'lucide-react';
import { useState } from 'react';

export function Header() {
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = user
    ? user.rol === 'PROVEEDOR'
      ? [
          { path: '/profesional/dashboard', label: 'Dashboard', icon: LayoutDashboard },
          { path: '/profesional/turnos', label: 'Mis Turnos', icon: Calendar },
          { path: '/profesional/historial', label: 'Historial', icon: HistoryIcon },
          { path: '/profesional/perfil', label: 'Mi Perfil', icon: User },
          { path: '/profesional/servicios', label: 'Servicios', icon: Building2 },
          { path: '/profesional/disponibilidad', label: 'Disponibilidad', icon: Settings },
        ]
      : user.rol === 'ADMIN'
        ? [
            { path: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
            { path: '/admin/turnos', label: 'Todos los Turnos', icon: Calendar },
            { path: '/admin/profesionales', label: 'Profesionales', icon: Building2 },
          ]
        : [
            { path: '/cliente/dashboard', label: 'Dashboard', icon: LayoutDashboard },
            { path: '/cliente/reservar', label: 'Reservar', icon: Calendar },
            { path: '/cliente/mis-turnos', label: 'Mis Turnos', icon: Calendar },
            { path: '/cliente/perfil', label: 'Mi Perfil', icon: User },
          ]
    : [];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-gray-200 dark:border-gray-700 bg-white/95 dark:bg-gray-900/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" aria-label="Main navigation">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2" aria-label="Agendame Home">
              <svg className="h-8 w-8 text-indigo-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM9 10H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm-8 4H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2z"/>
              </svg>
              <span className="text-xl font-bold text-gray-900 dark:text-white">Agendame</span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex lg:items-center lg:gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-2 whitespace-nowrap px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
                        : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                    )
                  }
                >
                  <item.icon className="h-4 w-4" aria-hidden="true" />
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>

          {/* Right side - Auth/User */}
          <div className="flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-4">
                <div className="hidden xl:flex xl:items-center gap-3 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <User className="h-5 w-5 text-gray-400" aria-hidden="true" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {user.nombre}
                  </span>
                  <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
                    {user.rol}
                  </span>
                </div>
                <Button variant="ghost" size="sm" onClick={logout}>
                  <LogOut className="h-4 w-4" aria-hidden="true" />
                  <span className="hidden sm:inline">Salir</span>
                </Button>
              </div>
            ) : (
              <div className="hidden sm:flex sm:items-center sm:gap-3">
                <Link to="/login">
                  <Button variant="ghost" size="sm">Iniciar sesión</Button>
                </Link>
                <Link to="/register">
                  <Button size="sm">Registrarse</Button>
                </Link>
              </div>
            )}

            {/* Mobile menu button */}
            <button
              className="lg:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-menu"
              aria-label={mobileMenuOpen ? 'Cerrar menú' : 'Abrir menú'}
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div id="mobile-menu" className="lg:hidden py-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex flex-col gap-2">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
                        : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                    )
                  }
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <item.icon className="h-5 w-5" aria-hidden="true" />
                  {item.label}
                </NavLink>
              ))}
              {!user && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700 flex flex-col gap-2">
                  <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                    <Button variant="outline" className="w-full justify-start">Iniciar sesión</Button>
                  </Link>
                  <Link to="/register" onClick={() => setMobileMenuOpen(false)}>
                    <Button className="w-full justify-start">Registrarse</Button>
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}