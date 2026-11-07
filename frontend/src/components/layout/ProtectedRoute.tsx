import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Spinner } from '@/components/ui/misc';
import type { User } from '@/types';

interface ProtectedRouteProps {
  allowedRoles?: User['rol'][];
  children: React.ReactNode;
}

export function ProtectedRoute({ allowedRoles, children }: ProtectedRouteProps) {
  const { user, isLoading, cerroSesion } = useAuth();
  const location = useLocation();

  if (isLoading) return <Spinner className="min-h-screen items-center" />;

  if (!user) {
    // Si cerró sesión a propósito va a la home; si no (sin sesión o vencida), al login.
    if (cerroSesion) return <Navigate to="/" replace />;
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.rol)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
