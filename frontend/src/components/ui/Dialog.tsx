import { useEffect, useId, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';

interface DialogProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

/**
 * Diálogo modal simple: overlay fijo, cierra con Escape, con el botón o
 * tocando fuera, y pone el foco en el primer campo al abrirse. Se renderiza en
 * un portal sobre <body> para que ningún contenedor padre recorte el overlay.
 */
export function Dialog({ open, title, onClose, children }: DialogProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  // Ref para no re-ejecutar el efecto (y robar el foco) cuando cambia onClose
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCloseRef.current();
    };
    document.addEventListener('keydown', onKey);
    const primero = panelRef.current?.querySelector<HTMLElement>(
      'input, textarea, select, button:not([data-dialog-close])'
    );
    primero?.focus();
    return () => document.removeEventListener('keydown', onKey);
  }, [open]);

  if (!open) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-lg bg-white p-5 text-gray-900 shadow-xl dark:bg-gray-900 dark:text-gray-100"
      >
        <div className="mb-4 flex items-start justify-between gap-2">
          <h2 id={titleId} className="text-lg font-semibold">{title}</h2>
          <button
            type="button"
            data-dialog-close
            onClick={onClose}
            aria-label="Cerrar"
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        {children}
      </div>
    </div>,
    document.body
  );
}
