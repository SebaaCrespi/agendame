import { useEffect, useState } from 'react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { Link } from 'react-router-dom';
import { CalendarDays } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { ESTADO_COLOR, ESTADO_LABEL } from '@/components/turnos/estado';
import { cn } from '@/utils/cn';
import { formatHora } from '@/utils/horaNegocio';
import type { Turno, TurnoEstado } from '@/types';

export function ProfesionalDashboard() {
  const { user } = useAuth();
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const hoy = format(new Date(), 'yyyy-MM-dd');
    api
      .getMisTurnosProfesional({ desde: hoy, hasta: hoy, page: 1, size: 100 })
      .then((data) => setTurnos(data.items))
      .catch(() => setError('No se pudieron cargar los turnos de hoy'))
      .finally(() => setLoading(false));
  }, []);

  const conteo = turnos.reduce<Partial<Record<TurnoEstado, number>>>((acc, t) => {
    acc[t.estado] = (acc[t.estado] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Hola, {user?.nombre}</h1>
        <p className="mt-1 capitalize text-gray-600 dark:text-gray-400">
          {format(new Date(), "EEEE d 'de' MMMM", { locale: es })}
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {(Object.keys(conteo) as TurnoEstado[]).map((e) => (
          <span key={e} className={cn('rounded border px-2 py-1 text-sm', ESTADO_COLOR[e])}>
            {ESTADO_LABEL[e]}: {conteo[e]}
          </span>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between gap-2">
            <span>Turnos de hoy</span>
            <Link to="/profesional/turnos" className="flex items-center gap-1 text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400">
              <CalendarDays className="h-4 w-4" /> Ver grilla semanal
            </Link>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="py-6 text-center text-gray-500">Cargando…</p>
          ) : error ? (
            <p className="py-6 text-center text-red-600">{error}</p>
          ) : turnos.length === 0 ? (
            <p className="py-6 text-center text-gray-500">No tenés turnos hoy.</p>
          ) : (
            <ul className="divide-y divide-gray-100 dark:divide-gray-800">
              {turnos.map((t) => (
                <li key={t.id} className="flex flex-wrap items-center justify-between gap-2 py-3 text-gray-900 dark:text-gray-100">
                  <div>
                    <p className="font-medium">
                      {formatHora(t.fecha_inicio)} – {formatHora(t.fecha_fin)} · {t.cliente_nombre}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{t.servicio_nombre}</p>
                  </div>
                  <span className={cn('rounded border px-2 py-0.5 text-xs', ESTADO_COLOR[t.estado])}>
                    {ESTADO_LABEL[t.estado]}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
