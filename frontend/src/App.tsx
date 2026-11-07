import { BrowserRouter, Navigate, Route, Routes, useLocation, useSearchParams } from 'react-router-dom';
import { destinoSeguro } from '@/utils/destino';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AppShell } from '@/components/layout/AppShell';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { PublicLayout } from '@/components/layout/PublicLayout';
import { HOME_POR_ROL } from '@/components/layout/nav';
import { Spinner } from '@/components/ui/misc';
import { LandingPage } from '@/pages/LandingPage';
import { LoginPage } from '@/pages/auth/LoginPage';
import { RegisterPage } from '@/pages/auth/RegisterPage';
import { ClienteInicioPage } from '@/pages/cliente/InicioPage';
import { ReservarPage } from '@/pages/cliente/ReservarPage';
import { MisTurnosPage } from '@/pages/cliente/MisTurnosPage';
import { ProfesionalHoyPage } from '@/pages/profesional/HoyPage';
import { ProfesionalAgendaPage } from '@/pages/profesional/AgendaPage';
import { ProfesionalHistorialPage } from '@/pages/profesional/HistorialPage';
import { ConfiguracionLayout } from '@/pages/profesional/ConfiguracionLayout';
import { ProfesionalPerfilPage } from '@/pages/profesional/PerfilPage';
import { ProfesionalServiciosPage } from '@/pages/profesional/ServiciosPage';
import { ProfesionalDisponibilidadPage } from '@/pages/profesional/DisponibilidadPage';
import { AdminResumenPage } from '@/pages/admin/ResumenPage';
import { AdminProfesionalesPage } from '@/pages/admin/ProfesionalesPage';
import { AdminTurnosPage } from '@/pages/admin/TurnosPage';

/** "/": landing para visitantes, panel del rol para usuarios con sesión. */
function Home() {
  const { isLoading, user } = useAuth();
  if (isLoading) return <Spinner className="min-h-screen items-center" />;
  return user ? <Navigate to={HOME_POR_ROL[user.rol]} replace /> : <LandingPage />;
}

/** Reserva sin cuenta: un cliente con sesión va a su versión dentro del panel. */
function ReservaPublica() {
  const { isLoading, user } = useAuth();
  const { search } = useLocation();
  if (isLoading) return <Spinner />;
  if (user?.rol === 'CLIENTE') return <Navigate to={`/cliente/reservar${search}`} replace />;
  return <ReservarPage />;
}

/** Login y registro: con sesión se sale, a `?next=` si lo hay (ej. volver a la reserva) o al panel. */
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isLoading, user } = useAuth();
  const [params] = useSearchParams();
  if (isLoading) return <Spinner className="min-h-screen items-center" />;
  if (user) return <Navigate to={destinoSeguro(params.get('next')) ?? '/'} replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
      <Route element={<PublicLayout />}>
        <Route path="/reservar" element={<ReservaPublica />} />
      </Route>

      {/* Cliente */}
      <Route
        path="/cliente"
        element={
          <ProtectedRoute allowedRoles={['CLIENTE']}>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="inicio" replace />} />
        <Route path="inicio" element={<ClienteInicioPage />} />
        <Route path="reservar" element={<ReservarPage />} />
        <Route path="mis-turnos" element={<MisTurnosPage />} />
        <Route path="dashboard" element={<Navigate to="/cliente/inicio" replace />} />
      </Route>

      {/* Profesional */}
      <Route
        path="/profesional"
        element={
          <ProtectedRoute allowedRoles={['PROVEEDOR']}>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="hoy" replace />} />
        <Route path="hoy" element={<ProfesionalHoyPage />} />
        <Route path="agenda" element={<ProfesionalAgendaPage />} />
        <Route path="historial" element={<ProfesionalHistorialPage />} />
        <Route path="configuracion" element={<ConfiguracionLayout />}>
          <Route index element={<Navigate to="servicios" replace />} />
          <Route path="servicios" element={<ProfesionalServiciosPage />} />
          <Route path="disponibilidad" element={<ProfesionalDisponibilidadPage />} />
          <Route path="perfil" element={<ProfesionalPerfilPage />} />
        </Route>
        {/* Rutas anteriores al rediseño */}
        <Route path="dashboard" element={<Navigate to="/profesional/hoy" replace />} />
        <Route path="turnos" element={<Navigate to="/profesional/agenda" replace />} />
        <Route path="servicios" element={<Navigate to="/profesional/configuracion/servicios" replace />} />
        <Route path="disponibilidad" element={<Navigate to="/profesional/configuracion/disponibilidad" replace />} />
        <Route path="perfil" element={<Navigate to="/profesional/configuracion/perfil" replace />} />
      </Route>

      {/* Admin */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={['ADMIN']}>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="resumen" replace />} />
        <Route path="resumen" element={<AdminResumenPage />} />
        <Route path="turnos" element={<AdminTurnosPage />} />
        <Route path="profesionales" element={<AdminProfesionalesPage />} />
        <Route path="dashboard" element={<Navigate to="/admin/resumen" replace />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}
