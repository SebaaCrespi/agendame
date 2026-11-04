import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from './Button';

interface PaginacionProps {
  page: number;
  pages: number;
  onChange: (page: number) => void;
}

/** Anterior / "Página X de Y" / siguiente. No se muestra con una sola página. */
export function Paginacion({ page, pages, onChange }: PaginacionProps) {
  if (pages <= 1) return null;
  return (
    <nav className="mt-6 flex items-center justify-center gap-2" aria-label="Paginación">
      <Button variant="outline" size="sm" aria-label="Página anterior" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        <ChevronLeft className="h-4 w-4" />
      </Button>
      <span className="text-sm text-gray-600 dark:text-gray-400">
        Página {page} de {pages}
      </span>
      <Button variant="outline" size="sm" aria-label="Página siguiente" disabled={page >= pages} onClick={() => onChange(page + 1)}>
        <ChevronRight className="h-4 w-4" />
      </Button>
    </nav>
  );
}
