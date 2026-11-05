import { AlertCircle, CheckCircle } from 'lucide-react';
import { cn } from '@/utils/cn';

interface AlertaProps {
  tipo: 'error' | 'ok';
  children: React.ReactNode;
  className?: string;
}

/** Aviso de error o de éxito en línea. */
export function Alerta({ tipo, children, className }: AlertaProps) {
  const Icono = tipo === 'error' ? AlertCircle : CheckCircle;
  return (
    <div
      role={tipo === 'error' ? 'alert' : 'status'}
      className={cn(
        'flex items-start gap-2 rounded-lg p-3 text-sm',
        tipo === 'error'
          ? 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300'
          : 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300',
        className
      )}
    >
      <Icono className="mt-0.5 h-4 w-4 shrink-0" /> <span>{children}</span>
    </div>
  );
}

/** Clases de los inputs nativos (select, time, date) para que combinen con `Input`. */
export const inputClass =
  'rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100';
