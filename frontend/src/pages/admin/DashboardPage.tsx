import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Building2, Calendar } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';

/** CU-10: resumen del administrador. */
export function AdminDashboardPage() {
  const { user } = useAuth();
  const [activos, setActivos] = useState<number | null>(null);
  const [inactivos, setInactivos] = useState<number | null>(null);

  useEffect(() => {
    // size 1: solo interesa el total de cada listado
    api.getProfesionalesAdmin({ size: 1, activo: true }).then((d) => setActivos(d.total)).catch(() => setActivos(null));
    api.getProfesionalesAdmin({ size: 1, activo: false }).then((d) => setInactivos(d.total)).catch(() => setInactivos(null));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Hola, {user?.nombre}</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">Administración de Agendame</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-500 dark:text-gray-400">Profesionales activos</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{activos ?? '—'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-500 dark:text-gray-400">Profesionales inactivos</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{inactivos ?? '—'}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          to="/admin/profesionales"
          className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-4 font-medium text-gray-900 hover:border-indigo-400 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
        >
          <Building2 className="h-5 w-5 text-indigo-600" /> Gestionar profesionales
        </Link>
        <Link
          to="/admin/turnos"
          className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-4 font-medium text-gray-900 hover:border-indigo-400 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
        >
          <Calendar className="h-5 w-5 text-indigo-600" /> Ver todos los turnos
        </Link>
      </div>
    </div>
  );
}
