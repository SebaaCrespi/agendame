import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { Layout } from '@/components/layout/Layout';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { LoginPage } from '@/pages/auth/LoginPage';
import { RegisterPage } from '@/pages/auth/RegisterPage';
import { ClienteDashboard } from '@/pages/cliente/DashboardPage';
import { ProfesionalDashboard } from '@/pages/profesional/DashboardPage';
import { ProfesionalTurnosPage } from '@/pages/profesional/TurnosPage';
import { ProfesionalHistorialPage } from '@/pages/profesional/HistorialPage';
import { ProfesionalPerfilPage } from '@/pages/profesional/PerfilPage';
import { ProfesionalServiciosPage } from '@/pages/profesional/ServiciosPage';
import { ProfesionalDisponibilidadPage } from '@/pages/profesional/DisponibilidadPage';
import { AdminDashboardPage } from '@/pages/admin/DashboardPage';
import { AdminProfesionalesPage } from '@/pages/admin/ProfesionalesPage';
import { AdminTurnosPage } from '@/pages/admin/TurnosPage';

const HOME_POR_ROL = {
  CLIENTE: '/cliente/dashboard',
  PROVEEDOR: '/profesional/dashboard',
  ADMIN: '/admin/dashboard',
} as const;

/** Lleva a cada usuario al panel de su rol (evita el loop "/" <-> ruta de otro rol). */
function RoleRedirect() {
  const { isLoading, user } = useAuth();
  if (isLoading) return null;
  return <Navigate to={user ? HOME_POR_ROL[user.rol] : '/login'} replace />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-600 border-t-transparent" />
      </div>
    );
  }

  if (user) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        }
      />

      {/* Protected routes - Cliente */}
      <Route
        path="/cliente/*"
        element={
          <ProtectedRoute allowedRoles={['CLIENTE']}>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/cliente/dashboard" replace />} />
        <Route path="dashboard" element={<ClienteDashboard />} />
        <Route path="reservar" element={<ClienteDashboard />} />
        <Route path="mis-turnos" element={<ClienteDashboard />} />
      </Route>

      {/* Protected routes - Profesional */}
      <Route
        path="/profesional/*"
        element={
          <ProtectedRoute allowedRoles={['PROVEEDOR']}>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/profesional/dashboard" replace />} />
        <Route path="dashboard" element={<ProfesionalDashboard />} />
        <Route path="turnos" element={<ProfesionalTurnosPage />} />
        <Route path="historial" element={<ProfesionalHistorialPage />} />
        <Route path="perfil" element={<ProfesionalPerfilPage />} />
        <Route path="servicios" element={<ProfesionalServiciosPage />} />
        <Route path="disponibilidad" element={<ProfesionalDisponibilidadPage />} />
      </Route>

      {/* Protected routes - Admin */}
      <Route
        path="/admin/*"
        element={
          <ProtectedRoute allowedRoles={['ADMIN']}>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/admin/dashboard" replace />} />
        <Route path="dashboard" element={<AdminDashboardPage />} />
        <Route path="turnos" element={<AdminTurnosPage />} />
        <Route path="profesionales" element={<AdminProfesionalesPage />} />
      </Route>

      {/* Default redirect */}
      <Route path="/" element={<RoleRedirect />} />
      <Route path="*" element={<RoleRedirect />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}