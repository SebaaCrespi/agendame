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
    <nav className="flex items-center justify-between gap-2 border-t border-line px-5 py-3" aria-label="Paginación">
      <span className="text-[13px] text-muted tabular">
        Página {page} de {pages}
      </span>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" aria-label="Página anterior" disabled={page <= 1} onClick={() => onChange(page - 1)}>
          <ChevronLeft /> Anterior
        </Button>
        <Button variant="outline" size="sm" aria-label="Página siguiente" disabled={page >= pages} onClick={() => onChange(page + 1)}>
          Siguiente <ChevronRight />
        </Button>
      </div>
    </nav>
  );
}
