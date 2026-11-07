import { Link, Outlet } from 'react-router-dom';
import { buttonClass } from '@/components/ui/Button';
import { Brand } from './Brand';
import { ThemeSwitch } from './ThemeToggle';

/** Layout para visitantes sin sesión (reserva pública). */
export function PublicLayout() {
  return (
    <div className="min-h-screen bg-canvas">
      <header className="sticky top-0 z-30 border-b border-line bg-canvas/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Brand />
          <nav className="flex items-center gap-1 sm:gap-2" aria-label="Cuenta">
            <ThemeSwitch />
            <Link to="/login" className={buttonClass('ghost', 'md', 'hidden sm:inline-flex')}>
              Iniciar sesión
            </Link>
            <Link to="/register" className={buttonClass('outline', 'md')}>
              Crear cuenta
            </Link>
          </nav>
        </div>
      </header>
      <main id="contenido" className="mx-auto w-full max-w-6xl px-4 pb-16 pt-6 sm:px-6 md:pt-8">
        <Outlet />
      </main>
    </div>
  );
}
